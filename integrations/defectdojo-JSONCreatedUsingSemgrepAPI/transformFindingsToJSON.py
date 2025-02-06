import requests
import json
import os
from uploadSemgrepJSONToDefectDojo import uploadToDefectDojo
# Configuration
deployment_slug = "swati"
BASE_URL = "https://semgrep.dev"
findings_url = f"{BASE_URL}/api/v1/deployments/"+deployment_slug+"/findings&dedup=true
token = os.environ["SEMGREP_API_TOKEN"]
OUTPUT_FILE = "semgrep_findings_formatted.json"

def retrieve_paginated_data(endpoint, kind, page_size, headers):
    """
    Generalized function to retrieve multiple pages of data.
    Returns all data as a JSON string (not a Python dict!) in the same format 
    as the API would if it weren't paginated.
    """
    # Initialize values
    data_list = []
    hasMore = True
    page = -1
    while (hasMore == True):
        page = page + 1
        page_string = ""
        if (kind == 'projects'):
            page_string = f"?page_size={page_size}&page={page}"
        else:
            page_string = f"&page_size={page_size}&page={page}"
        r = requests.get(f"{endpoint}{page_string}", headers=headers)
        if r.status_code != 200:
            sys.exit(f'Get failed: {r.text}')
        data = r.json()
        if not data.get(kind):
            print(f"At page {page} there is no more data of {kind}")
            hasMore = False
        data_list.extend(data.get(kind))
    return json.dumps({ f"{kind}": data_list})

def fetch_semgrep_findings():
    response = retrieve_paginated_data(findings_url, "findings", 3000, headers=headers)


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
        dd_url= "http://localhost:8080"
        product_name = "Semgrep SAST"
        engagement_name = "Semgrep Scans"
        report = OUTPUT_FILE
        uploadToDefectDojo("true", dd_token,dd_url, product_name, engagement_name, report)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
