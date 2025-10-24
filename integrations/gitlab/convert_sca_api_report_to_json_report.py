#!/usr/bin/env python3
import json, re, sys, hashlib
from pathlib import Path

# =========================
# Embedded SCC-SCA SCHEMA
# =========================
# This is the shape each "result" entry will have.
EMBEDDED_RESULT_SCHEMA = {
    "check_id": "N/A",
    "path": "N/A",
    "start": {"line": "N/A", "col": "N/A", "offset": "N/A"},
    "end": {"line": "N/A", "col": "N/A", "offset": "N/A"},
    "extra": {
        "metavars": {},
        "message": "N/A",
        "metadata": {
            "confidence": "N/A",
            "category": "N/A",
            "cve": "N/A",
            "cwe": ["N/A"],
            "ghsa": "N/A",
            "owasp": ["N/A"],
            "publish-date": "N/A",
            "references": ["N/A"],
            "sca-fix-versions": ["N/A"],
            "sca-kind": "N/A",
            "sca-schema": "N/A",
            "sca-severity": "N/A",
            "sca-vuln-database-identifier": "N/A",
            "technology": ["N/A"],
            "license": "N/A",
            "vulnerability_class": ["N/A"],
        },
    },
    "severity": "N/A",
    "fingerprint": "N/A",
    "lines": "N/A",
    "is_ignored": False,
    "sca_info": {
        "reachability_rule": False,
        "sca_finding_schema": "N/A",
        "dependency_match": {
            "dependency_pattern": {
                "ecosystem": "N/A",
                "package": "N/A",
                "semver_range": "N/A",
            },
            "found_dependency": {
                "package": "N/A",
                "version": "N/A",
                "ecosystem": "N/A",
                "allowed_hashes": {},
                "transitivity": "N/A",
                "lockfile_path": "N/A",
                "line_number": "N/A",
            },
            "lockfile": "N/A",
        },
        "reachable": False,
    },
    "engine_kind": "OSS",
}

EMBEDDED_TOPLEVEL = {
    "version": "1.140.0",
    "results": []
}

# =========================
# Helpers
# =========================
def parse_line_number_from_url(url: str):
    if not isinstance(url, str):
        return None
    m = re.search(r'#L(\d+)$', url)
    return int(m.group(1)) if m else None

def map_severity(api_sev: str) -> str:
    if not api_sev:
        return "N/A"
    s = api_sev.lower()
    if s in ("critical", "high", "medium", "moderate"):
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
    """Collect reference URLs/strings from common fields in finding/rule."""
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

    # Deduplicate preserving order
    seen, uniq = set(), []
    for r in refs:
        if r and r not in seen:
            seen.add(r)
            uniq.append(r)
    return uniq

def na_like(template_value):
    if isinstance(template_value, dict):
        return {k: na_like(v) for k, v in template_value.items()}
    if isinstance(template_value, list):
        return ["N/A"]
    # scalar
    return "N/A"

def shape_to_schema(template, obj):
    """Ensure obj has the exact keys as template (missing -> 'N/A' equivalents)."""
    if isinstance(template, dict):
        shaped = {}
        for k, v in template.items():
            if isinstance(v, dict):
                shaped[k] = shape_to_schema(v, obj.get(k) if isinstance(obj, dict) else {})
            elif isinstance(v, list):
                # If list in template, ensure a list. If empty or wrong type -> ["N/A"]
                src_val = obj.get(k) if isinstance(obj, dict) else None
                if isinstance(src_val, list) and len(src_val) > 0:
                    shaped[k] = src_val
                else:
                    shaped[k] = ["N/A"]
            else:
                # scalar in template
                val = obj.get(k) if isinstance(obj, dict) else None
                shaped[k] = val if (val is not None and not isinstance(val, (dict, list))) else "N/A"
        return shaped
    elif isinstance(template, list):
        return obj if isinstance(obj, list) and len(obj) > 0 else ["N/A"]
    else:
        return obj if (obj is not None and not isinstance(obj, (dict, list))) else "N/A"

# =========================
# Conversion
# =========================
def convert_one_finding(fnd: dict) -> dict:
    rule_block = fnd.get("rule") or {}
    loc = fnd.get("location") or {}

    rule_name = fnd.get("rule_name") or rule_block.get("name") or "N/A"
    file_path = loc.get("file_path") or "N/A"
    line = loc.get("line") or parse_line_number_from_url(fnd.get("line_of_code_url")) or 1
    col = loc.get("column") or 1
    end_line = loc.get("end_line") or line
    end_col = loc.get("end_column") or col

    message = fnd.get("rule_message") or rule_block.get("message") or "N/A"

    vuln_id = fnd.get("vulnerability_identifier") or "N/A"
    cwe_names = ensure_list(rule_block.get("cwe_names") or fnd.get("cwe_names")) or ["N/A"]
    owasp_names = ensure_list(rule_block.get("owasp_names") or fnd.get("owasp_names")) or ["N/A"]
    vuln_classes = ensure_list(rule_block.get("vulnerability_classes") or fnd.get("vulnerability_classes")) or ["N/A"]
    confidence = (rule_block.get("confidence") or fnd.get("confidence") or "N/A").upper()
    category = (rule_block.get("category") or "N/A")

    fd = fnd.get("found_dependency") or {}
    package = fd.get("package") if fd.get("package") is not None else None
    version = fd.get("version") if fd.get("version") is not None else None
    eco = fd.get("ecosystem") if fd.get("ecosystem") is not None else None
    lockfile_path = fd.get("lockfile_path") or (loc.get("file_path") or "N/A")
    lock_line = parse_line_number_from_url(fd.get("lockfile_line_url")) or (line if isinstance(line, int) else None)

    lines_str = f"{package}=={version}" if package and version else "N/A"

    fixes = []
    for fr in ensure_list(fnd.get("fix_recommendations")):
        p = fr.get("package") or package
        v = fr.get("version")
        if p and v:
            fixes.append({p: v})
    if not fixes:
        fixes = ["N/A"]

    reachability = fnd.get("reachability")
    reachable_flag = reachability_rule_flag(reachability)
    sca_kind = sca_kind_from_reachability(reachability)
    references = coalesce_references(fnd) or ["N/A"]

    fp = fnd.get("match_based_id") or fnd.get("syntactic_id")
    if not fp:
        h = hashlib.sha256(f"{rule_name}|{file_path}|{package}|{version}|{vuln_id}".encode()).hexdigest()
        fp = f"{h}_0"

    base = {
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
                "ghsa": fnd.get("ghsa") or (rule_block.get("ghsa") if isinstance(rule_block.get("ghsa"), str) else "N/A"),
                "owasp": owasp_names,
                "publish-date": fnd.get("publish_date") or rule_block.get("publish_date") or "N/A",
                "references": references,
                "sca-fix-versions": fixes,
                "sca-kind": sca_kind or "N/A",
                "sca-schema": 20230302,
                "sca-severity": (fnd.get("severity") or "N/A").upper() if fnd.get("severity") else "N/A",
                "sca-vuln-database-identifier": vuln_id,
                "technology": ensure_list(fnd.get("technology") or rule_block.get("technology")) or ["N/A"],
                "license": "Semgrep Rules License v1.0. For more details, visit semgrep.dev/legal/rules-license",
                "vulnerability_class": vuln_classes,
            },
        },
        "severity": map_severity(fnd.get("severity")) if fnd.get("severity") else "N/A",
        "fingerprint": fp or "N/A",
        "lines": lines_str,
        "is_ignored": False,
        "sca_info": {
            "reachability_rule": reachable_flag,
            "sca_finding_schema": 20220913,
            "dependency_match": {
                "dependency_pattern": {
                    "ecosystem": eco if eco is not None else "N/A",
                    "package": package if package is not None else "N/A",
                    "semver_range": "N/A",
                },
                "found_dependency": {
                    "package": package if package is not None else "N/A",
                    "version": version if version is not None else "N/A",
                    "ecosystem": eco if eco is not None else "N/A",
                    "allowed_hashes": {},
                    "transitivity": fd.get("transitivity") or "N/A",
                    "lockfile_path": lockfile_path or "N/A",
                    "line_number": lock_line if lock_line is not None else "N/A",
                },
                "lockfile": lockfile_path or "N/A",
            },
            "reachable": reachable_flag,
        },
        "engine_kind": "OSS",
    }

    # Finally, force the exact embedded schema (fill missing as "N/A")
    return shape_to_schema(EMBEDDED_RESULT_SCHEMA, base)

def convert(doc: dict) -> dict:
    out = json.loads(json.dumps(EMBEDDED_TOPLEVEL))  # deep copy
    findings = doc.get("findings") or []
    for f in findings:
        out["results"].append(convert_one_finding(f))
    return out

# =========================
# Main
# =========================
def main():
    if len(sys.argv) != 3:
        print("Usage: python convert_sca_to_scc_sca.py <sca-report.json> <output-report-scc-sca.json>")
        sys.exit(1)

    inp = Path(sys.argv[1])
    outp = Path(sys.argv[2])

    data = json.loads(inp.read_text(encoding="utf-8"))
    converted = convert(data)
    outp.write_text(json.dumps(converted, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {outp}")

if __name__ == "__main__":
    main()
