import json
import sys
from datetime import datetime

def conversion_semgrep_to_gitlab(report_semgrep, data):
    print("Populating Code findings data from Semgrep JSON report")
    with open(report_semgrep, 'r') as file_semgrep:
        data_semgrep = json.load(file_semgrep)
        for vuln in data_semgrep['results']:
            if not vuln['check_id'].startswith('ssc-'):

                links = [{"url": ref} for ref in vuln.get('extra').get('metadata')['references']]
                rule_name = vuln['check_id']

                new_vuln = {
                            "id": vuln.get('extra')['fingerprint'][0:63],
                            "name": rule_name[rule_name.rfind('.')+1:],
                            "description": vuln.get('extra')['message'],
                            "severity": get_severity(vuln), 
                            "location": {
                                "file": vuln.get('path'),
                                "start_line": vuln.get('start')['line'],
                                "end_line": vuln.get('end')['line'],
                            },
                            "identifiers": [
                                {
                                    "type": "semgrep_code",
                                    "name": vuln['check_id'],
                                    "value": vuln['check_id'],
                                    "url": vuln.get('extra').get('metadata').get('semgrep.dev').get('rule')['url']
                                }
                            ],
                            "links": links,
                            "details": {
                                "confidence": {
                                "name": "Confidence",
                                "type": "text",
                                "value": vuln.get('extra').get('metadata').get('confidence', "UNKNOWN")
                                }
                            },
                            "flags": get_flags(vuln)
                }
                data['vulnerabilities'].append(new_vuln)

        new_scan_info = get_new_scan_info(data_semgrep)
        data['scan'] = new_scan_info

    print("Dumping to a GitLab SAST JSON report")
    with open('gl-sast-report.json', 'w') as f:
        json.dump(data, f, indent=4)  # pretty print JSON

def get_severity(vuln):
    
    severity = vuln.get('extra')['severity']

    if severity == "INFO":
        severity = "Low"
    elif severity == "WARNING":
        severity = "Medium"
    elif severity == "ERROR":
        severity = "High"
    else:
        severity = "Unknown"
    
    return severity

def get_flags(vuln):

    all_flags = []
    
    if vuln.get('extra').get('metadata').get('confidence', "UNKNOWN") == "LOW":
        
        flag = {
            "description": "This finding is from a low confidence rule.",
            "origin": "Semgrep",
            "type": "flagged-as-likely-false-positive"
        }
        all_flags.append(flag)
    
    return all_flags


def get_new_scan_info(data):
    current_datetime = datetime.now()
    formatted_datetime = current_datetime.strftime("%Y-%m-%dT%H:%M:%S")
    # by having the `name` be "Code" and the `vendor` be "Semgrep", this looks good in the GitLab UI
    new_scan_info = {
        "analyzer": {
        "id": "semgrep_code_scan",
        "name": "Code",
        "url": "https://semgrep.dev",
        "vendor": {
            "name": "Semgrep"
        },
        "version": data['version']
        },
        "scanner": {
        "id": "semgrep_code_scan",
        "name": "Code",
        "url": "https://semgrep.dev",
        "vendor": {
            "name": "Semgrep"
        },
        "version": data['version']
        },
        "type": "sast",
        "start_time": formatted_datetime,
        "end_time": formatted_datetime,
        "status": "success"
    }
    return new_scan_info

if __name__ == "__main__":

    if len(sys.argv) == 2:
        report_semgrep = sys.argv[1]
    else:
        report_semgrep = "report-code.json" # adding a default value in case it's not supplied at runtime

    print("Starting conversion process from Semgrep JSON to GitLab SAST JSON")
    data = {
        "version": "15.0.0",
        "vulnerabilities": [],
        "scan": {}
    }

    conversion_semgrep_to_gitlab(report_semgrep, data)