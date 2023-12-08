import json
import sys
from datetime import datetime

def conversion_semgrep_to_gitlab(report_semgrep, data):
    print("Populating data from Semgrep JSON report")
    with open(report_semgrep, 'r') as file_semgrep:
        data_semgrep = json.load(file_semgrep)
        for vuln in data_semgrep['results']:
            
            links = []
            for ref in vuln.get('extra').get('metadata')['references']:
                link = {"url": ref}
                links.append(link)

            new_vuln = {
                        "id": vuln.get('extra')['fingerprint'][0:63],
                        "name": "Semgrep: " + vuln['check_id'],
                        "description": vuln.get('extra')['message'],
                        "cve": vuln.get('extra').get('metadata')['sca-vuln-database-identifier'],
                        "severity": get_severity(vuln),
                        "solution": "Upgrade dependencies to fixed versions: "+get_solution(vuln), 
                        "location": {
                            "file": vuln.get('extra').get('sca_info').get('dependency_match')['lockfile'],
                            "dependency": {
                            "package": {
                                "name": vuln.get('extra').get('sca_info').get('dependency_match').get('found_dependency')['package']
                            },
                            "version": vuln.get('extra').get('sca_info').get('dependency_match').get('found_dependency')['version']
                            }
                        },
                        "identifiers": [
                            {
                                "type": "cve",
                                "name": vuln.get('extra').get('metadata')['sca-vuln-database-identifier'],
                                "value": vuln.get('extra').get('metadata')['sca-vuln-database-identifier'],
                                "url": "https://cve.mitre.org/cgi-bin/cvename.cgi?name="+vuln.get('extra').get('metadata')['sca-vuln-database-identifier']
                            }
                        ],
                        "links": links,
                        "details": {
                            "vulnerable_package": {
                            "type": "text",
                            "name": "Vulnerable Package",
                            "value": vuln.get('extra').get('sca_info').get('dependency_match').get('found_dependency')['package'] 
                            + ":" + vuln.get('extra').get('sca_info').get('dependency_match').get('found_dependency')['version'] 
                        }
                    }
                        
            }
            data['vulnerabilities'].append(new_vuln)

        for vuln in data_semgrep['results']:
            new_file = { "path": vuln.get('extra').get('sca_info').get('dependency_match')['lockfile'],
                        "package_manager": vuln.get('extra').get('sca_info').get('dependency_match').get('dependency_pattern')['ecosystem'],
                        "dependencies": [
                            {
                            "package": {
                                "name": vuln.get('extra').get('sca_info').get('dependency_match').get('found_dependency')['package'] 
                            },
                            "version": vuln.get('extra').get('sca_info').get('dependency_match').get('found_dependency')['version'] 
                            }
                        ]
            }
            data['dependency_files'].append(new_file)

        new_scan_info = get_new_scan_info(data_semgrep)
        data['scan'] = new_scan_info

    print("Dumping to a GitLab JSON report")
    with open('gl-dependency-scanning-report.json', 'w') as f:
        json.dump(data, f, indent=4)  # pretty print JSON

def get_severity(vuln):
    severity = to_hungarian_case(vuln.get('extra').get('metadata')['sca-severity'])
    kind = vuln.get('extra').get('metadata')['sca-kind']
    if kind == "reachable":
        severity = "Critical"
    else:
        if severity == "Moderate":
            severity = "Medium"
    return severity

def get_solution(vuln):
    sca_fix_versions = vuln.get('extra').get('metadata').get('sca-fix-versions', [])
    
    if not sca_fix_versions:
        return "No known fixed versions"

    solution_string = ""
    for sol in sca_fix_versions:
        solution_string = str(sol)[1:-1].replace("'", "")
    
    return solution_string

def get_new_scan_info(data):
    current_datetime = datetime.now()
    formatted_datetime = current_datetime.strftime("%Y-%m-%dT%H:%M:%S")
    new_scan_info = {
        "analyzer": {
        "id": "semgrep",
        "name": "Semgrep",
        "url": "https://semgrep.dev",
        "vendor": {
            "name": "Semgrep"
        },
        "version": data['version']
        },
        "scanner": {
        "id": "semgrep",
        "name": "Semgrep",
        "url": "https://semgrep.dev",
        "vendor": {
            "name": "Semgrep"
        },
        "version": data['version']
        },
        "type": "dependency_scanning",
        "start_time": formatted_datetime,
        "end_time": formatted_datetime,
        "status": "success"
    }
    return new_scan_info

def to_hungarian_case(input_string):
    hungarian_case_words = input_string[0].upper() + input_string[1:].lower()
    return hungarian_case_words



if __name__ == "__main__":

    if len(sys.argv) == 2:
        report_semgrep = sys.argv[1]
    else:
        report_semgrep = "report-ssc.json" # adding a default value in case it's not supplied at runtime

    print("Starting conversion process from Semgrep JSON to GitLab JSON")
    data = {
        "version": "15.0.0",
        "vulnerabilities": [],
        "dependency_files": [],
        "scan": {}
    }

    conversion_semgrep_to_gitlab(report_semgrep, data)
