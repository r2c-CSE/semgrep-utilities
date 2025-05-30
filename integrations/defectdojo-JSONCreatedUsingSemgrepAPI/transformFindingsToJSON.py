import requests
import json
import os
import sys
import argparse

SEMGREP_APP_TOKEN = os.environ["SEMGREP_APP_TOKEN"]

def retrieve_paginated_data(endpoint,pg_size):
    all_findings = []
    page = 0
    page_size = pg_size
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
            print("No more findings.")
            break 

        all_findings.extend(findings)
        page += 1  # Go to the next page

    return  {"findings": all_findings}


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
    parser = argparse.ArgumentParser(description="Fetch Semgrep findings and format them for DefectDojo.")
    parser.add_argument("--deployment_slug", required=True, 
                        help="The slug of the Semgrep deployment. This argument is required.")
    parser.add_argument("--base_url", default="https://semgrep.dev", 
                        help="The base URL of the Semgrep API (e.g., 'https://semgrep.dev').")
    parser.add_argument("--output_file", default="report.json", 
                        help="The name of the output JSON file.")
    parser.add_argument("--page_size", default=100, 
                        help="Maximum number of records per returned page. If not specified, defaults to 100 records.")
    args = parser.parse_args()

    # Construct findings_url using parsed arguments
    findings_url = f"{args.base_url}/api/v1/deployments/{args.deployment_slug}/findings"
    
    try:
        semgrep_data =  retrieve_paginated_data(findings_url,args.page_size)
        formatted_data = format_findings_for_dd(semgrep_data)
        save_to_file(formatted_data, args.output_file)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
