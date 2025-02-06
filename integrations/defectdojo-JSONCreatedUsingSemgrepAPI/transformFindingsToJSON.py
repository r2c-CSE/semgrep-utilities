import requests
import json
import os
from uploadSemgrepJSONToDefectDojo import uploadToDefectDojo
# Configuration
SEM_GREP_API_URL = "https://semgrep.dev/api/v1/deployments/swati/findings"
token = os.environ["SEMGREP_API_TOKEN"]

OUTPUT_FILE = "semgrep_findings_formatted.json"

def fetch_semgrep_findings():
    headers = {
       "Authorization": "Bearer " + token,
    }

    response = requests.get(SEM_GREP_API_URL, headers=headers)
    response.raise_for_status()
    return response.json()

def format_findings_for_dd(semgrep_data):
    formatted_findings = []

    for item in semgrep_data.get("findings", []):
        finding = {
            "check_id": item["rule_name"],
            "path": item["location"]["file_path"],
            "start": {
                "line": item["location"]["line"],
                "col": item["location"]["column"],
            },
            "end": {
                "line": item["location"]["end_line"],
                "col": item["location"]["end_column"],
            },
            "extra": {
                "message": item["rule_message"],
                "severity": item["severity"].capitalize(),
                "metadata": {
                    "cwe": item["rule"].get("cwe_names", []),
                    "owasp": item["rule"].get("owasp_names", []),
                },
                "fix": None,
                "lines": item["line_of_code_url"],  # Placeholder, as API doesn't provide line snippets
            },
        }
        formatted_findings.append(finding)

    return {"results": formatted_findings, "errors": []}

def save_to_file(data, filename):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)
    print(f"Findings saved to {filename}")

def main():
    try:
        semgrep_data = fetch_semgrep_findings()
        formatted_data = format_findings_for_dd(semgrep_data)
        save_to_file(formatted_data, OUTPUT_FILE)
        uploadToDefectDojo("true", "c161ed6ca2152aa4f19490cd8b9f171e5b2e37c7", "http://localhost:8080", "Semgrep SAST", "Semgrep Scans", "semgrep_findings_formatted.json")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
