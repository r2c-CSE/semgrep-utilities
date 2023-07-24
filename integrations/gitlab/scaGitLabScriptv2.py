import json



def conversion_semgrep_to_gitlab(data):
    print("Populating data from Semgrep JSON report")
    with open('integrations/gitlab/report-ssc.json', 'r') as file_semgrep:
        data_semgrep = json.load(file_semgrep)
        for vuln in data_semgrep['results']:
            new_vuln = {"id": vuln.get('extra')['fingerprint'],
                        "name": vuln['check_id'],
                        "description": vuln.get('extra')['message'],
                        "cve": vuln.get('extra').get('metadata')['sca-vuln-database-identifier'],
                        "severity": vuln.get('extra').get('metadata')['sca-severity'],
                        "solution": vuln.get('extra').get('metadata')['sca-fix-versions'][0] ## TODO: get all solutions 
                        }
            data['vulnerabilities'].append(new_vuln)

        for vuln in data_semgrep['results']:
            new_file = { "path": vuln.get('extra').get('sca_info').get('dependency_match')['lockfile'],
                        "package_manager": vuln.get('extra').get('sca_info').get('dependency_match').get('dependency_pattern')['ecosystem']
            }
            data['dependency_files'].append(new_file)

        new_scan_info = get_new_scan_info(data_semgrep)
        data['scan'] = new_scan_info

    print("Dumping to a GitLab JSON report")
    print(data)
    with open('gl-dependency-scanning-report.json', 'w') as f:
        json.dump(data, f, indent=4)  # pretty print JSON


def get_new_scan_info(data):
    new_scan_info = {
        "analyzer": {
        "id": "semgrep",
        "name": "semgrep",
        "url": "https://semgrep.dev",
        "vendor": {
            "name": "Semgrep"
        },
        "version": data['version']
        },
        "scanner": {
        "id": "semgrep",
        "name": "semgrep",
        "url": "https://semgrep.dev",
        "vendor": {
            "name": "Semgrep"
        },
        "version": data['version']
        },
        "type": "dependency_scanning",
        "start_time": "2023-07-20T14:54:46",
        "end_time": "2023-07-20T14:55:01",
        "status": "success"
    }
    return new_scan_info


print("Starting conversion process from Semgrep JSON to GitLab JSON")
data = {
    "version": "15.0.0",
    "vulnerabilities": [],
    "dependency_files": [],
    "scan": {}
}
conversion_semgrep_to_gitlab(data)