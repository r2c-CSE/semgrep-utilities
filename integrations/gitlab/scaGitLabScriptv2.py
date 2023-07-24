import json
import sys


def conversion_semgrep_to_gitlab(report_semgrep, data):
    print("Populating data from Semgrep JSON report")
    with open(report_semgrep, 'r') as file_semgrep:
        data_semgrep = json.load(file_semgrep)
        for vuln in data_semgrep['results']:
            new_vuln = {"id": vuln.get('extra')['fingerprint'],
                        "name": vuln['check_id'],
                        "description": vuln.get('extra')['message'],
                        "cve": vuln.get('extra').get('metadata')['sca-vuln-database-identifier'],
                        "severity": vuln.get('extra').get('metadata')['sca-severity'],
                        "solution": vuln.get('extra').get('metadata')['sca-fix-versions'][0], ## TODO: get all solutions 
                        "location": {
                            "file": "pom.xml",
                            "dependency": {
                            "package": {
                                "name": "org.apache.logging.log4j/log4j-core"
                            },
                            "version": "2.6.1"
                            }
                        },
                        "identifiers": [
                            {
                            "type": "gemnasium",
                            "name": "Gemnasium-ef60b3d6-926c-472f-b24a-f585deccf8b6",
                            "value": "ef60b3d6-926c-472f-b24a-f585deccf8b6",
                            "url": "https://gitlab.com/gitlab-org/security-products/gemnasium-db/-/blob/master/maven/org.apache.logging.log4j/log4j-core/CVE-2017-5645.yml"
                            },
                            {
                            "type": "cve",
                            "name": "CVE-2017-5645",
                            "value": "CVE-2017-5645",
                            "url": "https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2017-5645"
                            },
                            {
                            "type": "ghsa",
                            "name": "GHSA-fxph-q3j8-mv87",
                            "value": "GHSA-fxph-q3j8-mv87",
                            "url": "https://github.com/advisories/GHSA-fxph-q3j8-mv87"
                            }
                        ],
                        "links": [
                            {
                            "url": "http://www.openwall.com/lists/oss-security/2019/12/19/2"
                            }
                        ],
                        "details": {
                            "vulnerable_package": {
                            "type": "text",
                            "name": "Vulnerable Package",
                            "value": "org.apache.logging.log4j/log4j-core:2.6.1"
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
                                "name": "com.auth0/java-jwt"
                            },
                            "version": "3.18.0"
                            }
                        ]
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

if __name__ == "__main__":

    if len(sys.argv) == 2:
        report_semgrep = sys.argv[1]
    print("Starting conversion process from Semgrep JSON to GitLab JSON")
    data = {
        "version": "15.0.0",
        "vulnerabilities": [],
        "dependency_files": [],
        "scan": {}
    }
    conversion_semgrep_to_gitlab(report_semgrep, data)