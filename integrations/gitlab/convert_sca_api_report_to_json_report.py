#!/usr/bin/env python3
import json, re, sys, hashlib
from pathlib import Path

def parse_line_number_from_url(url: str):
    if not isinstance(url, str):
        return None
    m = re.search(r'#L(\d+)$', url)
    return int(m.group(1)) if m else None

def map_severity(api_sev: str) -> str:
    if not api_sev:
        return "WARNING"
    s = api_sev.lower()
    if s in ("critical", "high"):
        return "ERROR"
    if s in ("medium", "moderate"):
        return "ERROR"
    return "WARNING"

def reachability_rule_flag(reach: str) -> bool:
    if not reach:
        return False
    return any(k in reach.lower() for k in ["reachable", "conditionally"])

def sca_kind_from_reachability(reach: str) -> str:
    if not reach or reach.lower() in ("unreachable", "no reachability analysis"):
        return "upgrade-only"
    return "reachable"

def ensure_list(x):
    if x is None:
        return []
    return x if isinstance(x, list) else [x]

def coalesce_references(finding: dict) -> list:
    """Collect reference URLs/strings from a variety of common fields."""
    rule_block = finding.get("rule") or {}
    refs = []

    # Direct string/list fields
    for key in [
        "references", "reference_urls", "links", "urls", "advisory_urls",
        "documentation", "docs", "sources"
    ]:
        val = finding.get(key) or rule_block.get(key)
        if isinstance(val, str):
            refs.append(val)
        elif isinstance(val, list):
            refs.extend([v for v in val if isinstance(v, str)])

    # Nested advisory-ish structures
    for adv_key in ["advisories", "advisory", "vulnerabilities", "cve", "ghsa"]:
        adv = finding.get(adv_key) or rule_block.get(adv_key)
        if isinstance(adv, dict):
            for k in ["url", "reference", "link"]:
                if isinstance(adv.get(k), str):
                    refs.append(adv[k])
        elif isinstance(adv, list):
            for a in adv:
                if isinstance(a, dict):
                    for k in ["url", "reference", "link"]:
                        if isinstance(a.get(k), str):
                            refs.append(a[k])

    # Singular URL helpers
    for key in ["cve_url", "ghsa_url", "advisory_url"]:
        val = finding.get(key) or rule_block.get(key)
        if isinstance(val, str):
            refs.append(val)

    # Deduplicate, preserve order
    seen, uniq = set(), []
    for r in refs:
        if r and r not in seen:
            seen.add(r)
            uniq.append(r)
    return uniq

def convert(api_data: dict, tool_version: str = "1.140.0") -> dict:
    findings = api_data.get("findings") or []
    results = []

    for fnd in findings:
        rule_name = fnd.get("rule_name") or (fnd.get("rule") or {}).get("name") or "ssc-unknown"
        loc = fnd.get("location") or {}
        file_path = loc.get("file_path") or ""
        line = loc.get("line") or parse_line_number_from_url(fnd.get("line_of_code_url")) or 1
        col = loc.get("column") or 1
        end_line = loc.get("end_line") or line
        end_col = loc.get("end_column") or col

        rule_block = fnd.get("rule") or {}
        message = fnd.get("rule_message") or rule_block.get("message") or ""

        vuln_id = fnd.get("vulnerability_identifier")
        cwe_names = ensure_list(rule_block.get("cwe_names") or fnd.get("cwe_names"))
        owasp_names = ensure_list(rule_block.get("owasp_names") or fnd.get("owasp_names"))
        vuln_classes = ensure_list(rule_block.get("vulnerability_classes") or fnd.get("vulnerability_classes"))
        confidence = (rule_block.get("confidence") or fnd.get("confidence") or "LOW").upper()
        category = (rule_block.get("category") or "security").lower()

        fd = fnd.get("found_dependency") or {}
        package = fd.get("package")
        version = fd.get("version")
        eco = fd.get("ecosystem")
        lockfile_path = fd.get("lockfile_path") or (loc.get("file_path") or "")
        lock_line = parse_line_number_from_url(fd.get("lockfile_line_url")) or (line if isinstance(line, int) else None)

        lines_str = f"{package}=={version}" if package and version else ""

        fixes = []
        for fr in ensure_list(fnd.get("fix_recommendations")):
            p = fr.get("package") or package
            v = fr.get("version")
            if p and v:
                fixes.append({p: v})

        reachability = fnd.get("reachability")
        reachable_flag = reachability_rule_flag(reachability)
        sca_kind = sca_kind_from_reachability(reachability)
        references = coalesce_references(fnd)

        fp = fnd.get("match_based_id") or fnd.get("syntactic_id")
        if not fp:
            h = hashlib.sha256(f"{rule_name}|{file_path}|{package}|{version}|{vuln_id}".encode()).hexdigest()
            fp = f"{h}_0"

        results.append({
            "check_id": rule_name,
            "path": file_path,
            "start": {"line": line, "col": col, "offset": 0},
            "end": {"line": end_line, "col": end_col, "offset": 0},
            "extra": {
                "metavars": {},
                "message": message,
                "metadata": {
                    "confidence": confidence,
                    "category": category,
                    "cve": vuln_id,
                    "cwe": cwe_names,
                    "owasp": owasp_names,
                    "references": references,  # <-- now included
                    "sca-fix-versions": fixes,
                    "sca-kind": sca_kind,
                    "sca-schema": 20230302,
                    "sca-severity": (fnd.get("severity") or "LOW").upper(),
                    "sca-vuln-database-identifier": vuln_id,
                    "technology": ensure_list(fnd.get("technology") or rule_block.get("technology") or ["python"]),
                    "license": "Semgrep Rules License v1.0. For more details, visit semgrep.dev/legal/rules-license",
                    "vulnerability_class": vuln_classes,
                },
            },
            "severity": map_severity(fnd.get("severity")),
            "fingerprint": fp,
            "lines": lines_str,
            "is_ignored": False,
            "sca_info": {
                "reachability_rule": reachable_flag,
                "sca_finding_schema": 20220913,
                "dependency_match": {
                    "dependency_pattern": {
                        "ecosystem": eco,
                        "package": package,
                        "semver_range": None
                    },
                    "found_dependency": {
                        "package": package,
                        "version": version,
                        "ecosystem": eco,
                        "allowed_hashes": {},
                        "transitivity": fd.get("transitivity") or "unknown",
                        "lockfile_path": lockfile_path,
                        "line_number": lock_line
                    },
                    "lockfile": lockfile_path
                },
                "reachable": reachable_flag
            },
            "engine_kind": "OSS"
        })

    return {"version": tool_version, "results": results}

def main():
    inp = Path("sca-api-report.json")
    outp = Path("report-ssc.json")
    data = json.loads(Path(inp).read_text(encoding="utf-8"))
    converted = convert(data)
    outp.write_text(json.dumps(converted, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {outp}")

if __name__ == "__main__":
    main()
