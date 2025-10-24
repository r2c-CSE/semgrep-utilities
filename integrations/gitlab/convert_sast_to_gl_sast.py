import json
import uuid
from datetime import datetime

def convert_severity(severity):
    mapping = {
        "critical": "Critical",
        "high": "High",
        "medium": "Medium",
        "low": "Low",
        "info": "Info",
        "informational": "Info",
    }
    return mapping.get(severity.lower(), "Unknown")

def convert_confidence(confidence):
    mapping = {
        "high": "HIGH",
        "medium": "MEDIUM",
        "low": "LOW"
    }
    return mapping.get(confidence.lower(), "UNKNOWN")

def sast_to_gitlab(input_path, output_path):
    with open(input_path, "r") as f:
        semgrep_data = json.load(f)

    vulnerabilities = []
    for finding in semgrep_data.get("findings", []):
        rule_name = finding.get("rule_name")
        message = finding.get("rule_message")
        severity = convert_severity(finding.get("severity", ""))
        confidence = convert_confidence(finding.get("confidence", ""))

        file_path = finding.get("location", {}).get("file_path", "")
        start_line = finding.get("location", {}).get("line", 0)
        end_line = finding.get("location", {}).get("end_line", start_line)

        vuln = {
            "category": "sast",
            "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{file_path}:{rule_name}:{start_line}")),
            "message": message,
            "description": message,
            "severity": severity,
            "scanner": {
                "id": "semgrep",
                "name": "Semgrep",
                "vendor": {"name": "Semgrep"}
            },
            "location": {
                "file": file_path,
                "start_line": start_line,
                "end_line": end_line
            },
            "identifiers": [
                {
                    "type": "semgrep_type",
                    "name": f"Semgrep - {rule_name}",
                    "value": rule_name,
                    "url": f"https://semgrep.dev/r/{rule_name}"
                }
            ],
            "flags": [],
            "details": {
                "confidence": {
                    "type": "text",
                    "name": "confidence",
                    "value": confidence
                }
            }
        }
        vulnerabilities.append(vuln)

    gl_sast = {
        "$schema": "https://gitlab.com/gitlab-org/security-products/security-report-schemas/-/blob/master/dist/sast-report-format.json",
        "version": "15.0.4",
        "scan": {
            "start_time": datetime.utcnow().isoformat(),
            "end_time": datetime.utcnow().isoformat(),
            "analyzer": {
                "id": "semgrep",
                "name": "Semgrep",
                "url": "https://semgrep.dev",
                "version": "latest",
                "vendor": {"name": "Semgrep"}
            },
            "scanner": {
                "id": "semgrep",
                "name": "Semgrep",
                "url": "https://semgrep.dev",
                "version": "latest",
                "vendor": {"name": "Semgrep"}
            },
            "version": "latest",
            "status": "success",
            "type": "sast"
        },
        "vulnerabilities": vulnerabilities
    }

    with open(output_path, "w") as f:
        json.dump(gl_sast, f, indent=2)

    print(f"✅ Converted {len(vulnerabilities)} findings into GitLab SAST format → {output_path}")


if __name__ == "__main__":
    sast_to_gitlab("sast-api-report.json", "gl-sast-report.json")
