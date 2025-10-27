import json
import sys
import os
import getopt
import logging
from datetime import datetime
from collections import defaultdict

def conversion_semgrep_to_gitlab(report_semgrep, data, lowering_unreachable):
    print("Populating Supply Chain findings data from Semgrep JSON report")
    with open(report_semgrep, 'r') as file_semgrep:
        data_semgrep = json.load(file_semgrep)
        for vuln in data_semgrep['results']:
            if vuln['check_id'].startswith('ssc-'):

                links = [{"url": ref} for ref in vuln.get('extra').get('metadata')['references']]
                package_name = vuln.get('extra').get('sca_info').get('dependency_match').get('found_dependency')['package']
                # get the last CWE in the list of CWEs (if more than 1 exists)
                # if `cwe` does not exist, return empty list, if empty list, return list with default data
                cwe_title = (vuln.get('extra').get('metadata').get('cwe', []) or [' CWE data missing'])[-1]
                # snip the CWE string after the first space character so only the CWE title remains
                cwe_title = cwe_title[cwe_title.index(' ')+1:]

                new_vuln = {
                            "id": vuln.get('extra')['fingerprint'][0:63],
                            "name": package_name + " - " + cwe_title,
                            "description": vuln.get('extra')['message'],
                            "reachable": get_exposure(vuln),
                            "epss": get_epss(vuln),
                            "severity": get_severity(vuln, lowering_unreachable),
                            "solution": "Upgrade dependencies to fixed versions: "+get_solution(vuln), 
                            "location": {
                                # It gets the file path. It can be source code for reachable findings or the lockfile (manifest file) for other cases.
                                "file": vuln.get('path'),
                                "start_line": vuln.get('start').get('line'),
                                "end_line": vuln.get('end').get('line'),
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
                                },
                                {
                                    "type": "semgrep_ssc",
                                    "name": vuln['check_id'],
                                    "value": vuln['check_id'],
                                    "url": vuln.get('extra').get('metadata').get('semgrep.dev').get('rule')['url']
                                }
                            ],
                            "links": links,
                            "details": {
                                "vulnerable_package": {
                                    "type": "text",
                                    "name": "Vulnerable Package",
                                    "value": vuln.get('extra').get('sca_info').get('dependency_match').get('found_dependency')['package'] 
                                    + ":" + vuln.get('extra').get('sca_info').get('dependency_match').get('found_dependency')['version'] 
                                },
                                "exposure": {
                                    "type": "text",
                                    "name": "Exposure",
                                    "value": get_exposure(vuln)
                                },
                                "transitivity": {
                                    "type": "text",
                                    "name": "Transitivity",
                                    "value": vuln.get('extra').get('sca_info').get('dependency_match').get('found_dependency').get('transitivity', "UNKNOWN")
                                    
                                },
                                "confidence": {
                                    "type": "text",
                                    "name": "Confidence",
                                    "value": vuln.get('extra').get('metadata').get('confidence', "UNKNOWN")
                                }
                            },
                            "flags": get_flags(vuln)
                }
                data['vulnerabilities'].append(new_vuln)

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

    print("Dumping to a GitLab Dependency JSON report")
    with open('gl-dependency-scanning-report.json', 'w') as f:
        json.dump(data, f, indent=4)  # pretty print JSON

def get_severity(vuln, lowering_unreachable):
    severity = to_hungarian_case(vuln.get('extra').get('metadata')['sca-severity'])
    if severity == "Moderate":
        severity = "Medium"
    if lowering_unreachable == True:
        exposure = get_exposure(vuln)
        if exposure == "Unreachable":
            severity = "Info"
    return severity

def get_epss(vuln: dict) -> str:
    """
    Safely retrieves and formats the EPSS score from a vulnerability dictionary.

    Returns:
        str: The EPSS score as a percentage string (e.g., "42.3%")
             or "?" if the score is missing or invalid.
    """
    try:
        epss_data = vuln.get("epss_score") or {}
        score = epss_data.get("score")

        if score is None:
            return "?"

        # Ensure it's numeric before formatting
        if isinstance(score, (int, float)):
            return f"{score * 100:.2f}%"
        else:
            return "?"
    except Exception:
        return "?"


def get_exposure(vuln):

    sca_kind = vuln.get('extra').get('metadata').get('sca-kind', 'None')
    reachable = vuln.get('extra').get('sca_info')['reachable']

    if sca_kind == "upgrade-only":
        return "Reachable"
    elif sca_kind == "legacy":
        return "Undetermined"
    elif reachable:
        return "Reachable"
    else:
        return "Unreachable"

def get_flags(vuln):

    all_flags = []

    if get_exposure(vuln) == "Unreachable":
        
        flag = {
            "description": "Semgrep found no way to reach this vulnerability while scanning your code.",
            "origin": "Semgrep Supply Chain",
            "type": "flagged-as-likely-false-positive"
        }
        all_flags.append(flag)
    
    if vuln.get('extra').get('metadata').get('confidence', "UNKNOWN") == "LOW":
        
        flag = {
            "description": "This finding is from a low confidence rule.",
            "origin": "Semgrep Supply Chain",
            "type": "flagged-as-likely-false-positive"
        }
        all_flags.append(flag)
    
    return all_flags

def get_solution(vuln):
    sca_fix_versions = vuln.get('extra').get('metadata').get('sca-fix-versions', [])
    
    if not sca_fix_versions:
        return "No known fixed versions"

    # Use defaultdict to group versions by package name
    solutions = defaultdict(list)
    
    # Group versions by package
    for solution in sca_fix_versions:
        for package, version in solution.items():
            solutions[package].append(version)
    
    # Format the output with Markdown format
    formatted_solutions = []
    for package, versions in solutions.items():
        # Append the package and sorted versions as a Markdown list item
        formatted_solutions.append(f"- **{package}**: {', '.join(versions)};")

    # Join the lines for Markdown
    return "\n" + "\n".join(formatted_solutions)

def get_new_scan_info(data):
    current_datetime = datetime.now()
    formatted_datetime = current_datetime.strftime("%Y-%m-%dT%H:%M:%S")
    # by having the `name` be "Supply Chain" and the `vendor` be "Semgrep", this looks good in the GitLab UI
    new_scan_info = {
        "analyzer": {
        "id": "semgrep_dep_scan",
        "name": "Supply Chain",
        "url": "https://semgrep.dev",
        "vendor": {
            "name": "Semgrep"
        },
        "version": data['version']
        },
        "scanner": {
        "id": "semgrep_dep_scan",
        "name": "Supply Chain",
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

    logging.basicConfig(level=logging.INFO)
    if len(sys.argv) == 1:
        print('Usage: scaGitLabScript.py <json_file> [--lowering-unreachable true|false]')
        sys.exit()
    
    user_inputs = sys.argv[1:]
    lowering_unreachable = False  # Default to False unless explicitly set

    try:
        # Define options: 'h' for help, '--lowering-unreachable' which expects a value
        opts, args = getopt.getopt(user_inputs[1:], "h", ["lowering-unreachable=", "help"])
        
        if sys.argv[1].endswith('.json'):
            report_semgrep = sys.argv[1]
        else:
            print("Invalid file name. Your first argument must be a `*.json` file name.")
            sys.exit()

    except getopt.GetoptError as err:
        print(str(err))
        print('Usage: scaGitLabScript.py <json_file> [--lowering-unreachable true|false]')
        sys.exit(2)

    # Parse options
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print('Usage: scaGitLabScript.py <json_file> [--lowering-unreachable true|false]')
            sys.exit()
        elif opt == '--lowering-unreachable':
            if arg.lower() == 'true':
                lowering_unreachable = True
            elif arg.lower() == 'false':
                lowering_unreachable = False
            else:
                print('Invalid value for --lowering-unreachable. Use true or false.')
                sys.exit(2)

    print("Starting conversion process from Semgrep JSON to GitLab Dependency JSON")
    data = {
        "version": "15.0.0",
        "vulnerabilities": [],
        "dependency_files": [],
        "scan": {}
    }

    conversion_semgrep_to_gitlab(report_semgrep, data, lowering_unreachable)
