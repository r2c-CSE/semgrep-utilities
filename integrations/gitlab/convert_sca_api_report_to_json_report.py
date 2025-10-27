#!/usr/bin/env python3
"""
convert_sca_api_to_scan_sca.py

Converts a Semgrep SCA API report (sca-api-report.json) into the
"report-scan-sca.json" style (Semgrep results JSON with SCA fields).

Design goals:
- Keep ALL findings, even if some fields are missing.
- Match the structure of "report-scan-sca.json" (keys and nesting) as closely as possible.
- If a field is missing/not derivable, fill it with a sensible default:
  * Strings: "N/A"
  * Lists: []
  * Numbers: 0 / 0.0
  * Booleans: False
- Be defensive: never raise AttributeError on missing nested keys.
- Fingerprint: prefer "match_based_id" (API), fallback to "syntactic_id".
- Severity mapping: API severities ["critical","high"] -> "ERROR", everything else -> "WARNING".
- sca_info and metadata are populated from the API where possible.
- For the package name, if the API's found_dependency is missing, keep the structure but set package to None.

Usage:
    python convert_sca_api_to_scan_sca.py input.json output.json
"""

import json
import sys
import re
from typing import Any, Dict, List
from datetime import datetime

def safe_get(d: Any, path: List[str], default: Any = None) -> Any:
    cur = d
    for key in path:
        if isinstance(cur, dict) and key in cur:
            cur = cur[key]
        else:
            return default
    return cur

def to_semgrep_severity(api_sev: str) -> str:
    if not api_sev:
        return "WARNING"
    api_sev = str(api_sev).lower()
    return "ERROR" if api_sev in ("critical", "high") else "WARNING"

def parse_line_number_from_url(url: str) -> int:
    # Example: ".../requirements.txt#L15" -> 15
    if not url:
        return 0
    m = re.search(r"#L(\d+)", url)
    return int(m.group(1)) if m else 0

def eco_to_technology(eco: str) -> List[str]:
    mapping = {
        "pypi": ["python"],
        "npm": ["javascript"],
        "maven": ["java"],
        "rubygems": ["ruby"],
        "go": ["go"],
        "nuget": ["dotnet"],
        "packagist": ["php"],
    }
    if not eco:
        return []
    eco = eco.lower()
    return mapping.get(eco, [eco])

def build_metadata(f: Dict[str, Any]) -> Dict[str, Any]:
    rule = f.get("rule", {}) or {}
    found_dep = f.get("found_dependency", {}) or {}
    vuln_id = f.get("vulnerability_identifier") or "N/A"
    cve = vuln_id if isinstance(vuln_id, str) and vuln_id.upper().startswith("CVE-") else "N/A"
    owasp = rule.get("owasp_names") or []
    cwe = rule.get("cwe_names") or []
    vuln_classes = rule.get("vulnerability_classes") or []
    rule_name = rule.get("name") or []

    # Translate fix_recommendations list[{"package": "...", "version":"..."}] into
    # Semgrep's "sca-fix-versions" style: [{"<pkg>": "<ver>"}...]
    sca_fix_versions = []
    for rec in f.get("fix_recommendations") or []:
        pkg = rec.get("package")
        ver = rec.get("version")
        if pkg and ver:
            sca_fix_versions.append({pkg: ver})

    ecosystem = (found_dep.get("ecosystem") or "").lower()
    technology = eco_to_technology(ecosystem)

    metadata = {
        "confidence": rule.get("confidence") or f.get("confidence") or "N/A",
        "category": rule.get("category") or (f.get("categories") or ["N/A"])[0],
        "cve": cve,
        "cwe": cwe,
        "ghsa": "N/A",
        "owasp": owasp,
        "publish-date": "N/A",
        "references": [],
        "sca-fix-versions": sca_fix_versions,
        "sca-kind": "N/A",
        "sca-reachable-if": f.get("reachable_condition") or "",
        "sca-schema": 20230302,
        "sca-severity": get_sca_severity(f.get("severity")),
        "sca-vuln-database-identifier": vuln_id,
        "technology": technology,
        "license": "N/A",
        "vulnerability_class": vuln_classes,
        "semgrep.dev": {"rule": {"url": ""+"https://semgrep.dev/orgs/-/supply-chain/advisories?q="+rule_name}, "src": "unchanged"},
        "source": "N/A",
        "semgrep.url": "N/A",
        "dev.semgrep.actions": [],
    }
    return metadata

def get_sca_severity(severity: str) -> str:
    """Normalize SCA severity values to match expected naming conventions."""
    if not severity:
        return "UNKNOWN"

    mapping = {
        "LOW": "LOW",
        "MEDIUM": "MODERATE",
        "MODERATE": "MODERATE",
        "HIGH": "HIGH",
        "CRITICAL": "CRITICAL",
        "INFO": "INFO",
        "INFORMATIONAL": "INFO",
    }

    return mapping.get(severity.strip().upper(), "UNKNOWN")

def build_sca_info(f: Dict[str, Any]) -> Dict[str, Any]:
    loc = f.get("location", {}) or {}
    found_dep = f.get("found_dependency", {}) or {}
    lockfile_path = loc.get("file_path") or "N/A"
    line_num = parse_line_number_from_url((found_dep.get("lockfile_line_url") or ""))

    # Normalize reachability value for consistent comparison
    reachability_val = str(f.get("reachability", "")).strip().lower()
    is_reachable = reachability_val in {"reachable", "conditionally reachable", "always reachable"}

    # Build found_dependency structure; package can be None if missing
    fd_struct = {
        "package": found_dep.get("package"),
        "version": found_dep.get("version") or "latest",
        "ecosystem": found_dep.get("ecosystem") or "N/A",
        "allowed_hashes": {},
        "transitivity": found_dep.get("transitivity") or "unknown",
        "lockfile_path": lockfile_path,
        "line_number": line_num,
    }

    dep_pattern = {
        "ecosystem": found_dep.get("ecosystem") or "N/A",
        "package": found_dep.get("package"),
        "semver_range": "N/A",
    }

    sca_info = {
        "reachability_rule": is_reachable,
        "sca_finding_schema": 20220913,
        "dependency_match": {
            "dependency_pattern": dep_pattern,
            "found_dependency": fd_struct,
            "lockfile": lockfile_path,
        },
        "reachable": is_reachable,
    }

    return sca_info


def convert_finding(f: Dict[str, Any]) -> Dict[str, Any]:
    rule_name = f.get("rule_name") or f.get("rule", {}).get("name") or "N/A"
    loc = f.get("location", {}) or {}

    check_id = rule_name
    path = loc.get("file_path") or "N/A"

    start = {
        "line": int(loc.get("line") or 0),
        "col": int(loc.get("column") or 0),
        "offset": 0,
    }
    end = {
        "line": int(loc.get("end_line") or start["line"]),
        "col": int(loc.get("end_column") or start["col"]),
        "offset": 0,
    }

    # Prefer match_based_id for fingerprint; else syntactic_id; else a stable fallback
    fingerprint = (
        f.get("match_based_id")
        or f.get("syntactic_id")
        or f"finding-{f.get('id','unknown')}_0"
    )

    message = f.get("rule_message") or f.get("rule", {}).get("message") or "N/A"
    semgrep_sev = to_semgrep_severity(f.get("severity"))

    extra = {
        "metavars": {},
        "message": message,
        "metadata": build_metadata(f),
        "severity": semgrep_sev,
        "fingerprint": fingerprint,
        "lines": "N/A",
        "is_ignored": False,
        "sca_info": build_sca_info(f),
        "engine_kind": "OSS",
    }

    return {
        "check_id": check_id,
        "path": path,
        "start": start,
        "end": end,
        "extra": extra,
    }

def current_iso_no_ms():
    """Return current UTC time formatted as YYYY-MM-DDTHH:MM:SS"""
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")


def skeleton() -> Dict[str, Any]:
    # A minimal but structurally accurate shell for report-scan-sca.json
    now_str = current_iso_no_ms()
    return {
        "version": "latest",
        "results": [],
        "errors": [],
        "paths": {"scanned": [], "skipped": []},
        "time": {"start": now_str, "end": now_str, "max_memory_bytes": 0, "elapsed": 0.0},
        "engine_requested": ["supply-chain"],
        "interfile_languages_used": [],
        "skipped_rules": [],
        "subprojects": [],
    }

def convert(input_json: Dict[str, Any]) -> Dict[str, Any]:
    out = skeleton()
    findings = input_json.get("findings") or []
    out["results"] = [convert_finding(f) for f in findings]
    return out

def main():
    if len(sys.argv) < 3:
        print("Usage: python convert_sca_api_to_scan_sca.py <input_sca_api_report.json> <output_report_scan_sca.json>")
        sys.exit(1)

    in_path = sys.argv[1]
    out_path = sys.argv[2]

    with open(in_path, "r", encoding="utf-8") as f:
        input_json = json.load(f)

    output_json = convert(input_json)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output_json, f, indent=2, ensure_ascii=False)

    print(f"Wrote: {out_path}")

if __name__ == "__main__":
    main()
