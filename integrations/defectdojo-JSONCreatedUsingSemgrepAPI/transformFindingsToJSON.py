import requests
import json
import os
from uploadSemgrepJSONToDefectDojo import uploadToDefectDojo
import sys
# Configuration
deployment_slug = "swati"
BASE_URL = "https://semgrep.dev"
findings_url = BASE_URL+"/api/v1/deployments/"+deployment_slug+"/findings"
SEMGREP_APP_TOKEN = os.environ["SEMGREP_API_TOKEN"]
OUTPUT_FILE = "semgrep_findings_formatted.json"
dd_url= "http://localhost:8080"
product_name = "Semgrep SAST"
engagement_name = "Semgrep Scans"

def retrieve_paginated_data(endpoint):
    all_findings = []
    page = 0
    page_size = 100  # Adjust as needed
    headers = {"Accept": "application/json", "Authorization": "Bearer " + SEMGREP_APP_TOKEN}
    while True:
        response = requests.get(endpoint+"?&page_size="+str(page_size)+"&page="+str(page), headers=headers)
        
        if response.status_code != 200:
            print(f"Error: {response.status_code}, {response.text}")
            break  # Stop on failure
        try:
            data = response.json()
        except json.JSONDecodeError:
            print(f"Failed to parse JSON: {response.text}")
            break

        findings = data["findings"]
         # If findings list is empty, stop fetching more pages
        if not findings:
            print("No findings available.")
            break 

        all_findings.extend(findings)
        page += 1  # Go to the next page

    return  {"findings": all_findings}

def fetch_semgrep_findings():
    return retrieve_paginated_data(findings_url)

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
        dd_token = os.getenv("DEFECT_DOJO_API_TOKEN")
        report = OUTPUT_FILE
        uploadToDefectDojo("true", dd_token,dd_url, product_name, engagement_name, report)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
