import argparse
import json

def build_sarif_result_locations(finding):
    return [{
        "physicalLocation": {
            "artifactLocation": {
                "uri": finding['path'],
                "uriBaseId": "%SRCROOT%"
            },
            "region": {
                "endColumn": parse_loc_col(finding['end']),
                "endLine": finding['end']['line'],
                "snippet": {
                    "text": finding['extra']['lines']
                },
                "startColumn": parse_loc_col(finding['start']),
                "startLine": finding['start']['line']
            }
        }
    }]

def parse_loc_col(loc):
    return loc['col'] if (loc['col'] > 0) else 1

def parse_loc_cliloc(trace_item):
    loc_data = trace_item[1][0]
    return {
        "location": {
            "physicalLocation": {
                "artifactLocation": {
                    "uri": loc_data['path'],
                },
                "region": {
                    "endColumn": parse_loc_col(loc_data['end']),
                    "endLine": loc_data['end']['line'],
                    "startColumn": parse_loc_col(loc_data['start']),
                    "startLine": loc_data['start']['line'],
                    "snippet": { "text": trace_item[1][1] }
                }
            }
        },
        "nestingLevel": 0
    }

def parse_loc_no_label(trace_item):
    loc_data = trace_item[0]
    return {
        "location": {
            "physicalLocation": {
                "artifactLocation": {
                    "uri": loc_data['path'],
                },
                "region": {
                    "endColumn": parse_loc_col(loc_data['end']),
                    "endLine": loc_data['end']['line'],
                    "startColumn": parse_loc_col(loc_data['start']),
                    "startLine": loc_data['start']['line'],
                    "snippet": { "text": trace_item[1] }
                }
            }
        },
        "nestingLevel": 0
    }

def parse_loc_content(trace_item):
    loc_data = trace_item[0]['location']
    return {
        "location": {
            "physicalLocation": {
                "artifactLocation": {
                    "uri": loc_data['path'],
                },
                "region": {
                    "endColumn": parse_loc_col(loc_data['end']),
                    "endLine": loc_data['end']['line'],
                    "startColumn": parse_loc_col(loc_data['start']),
                    "startLine": loc_data['start']['line'],
                    "snippet": { "text": trace_item[0]['content'] }
                }
            }
        },
        "nestingLevel": 0
    }

def parse_loc_clicall(trace_item):
    return {}

def build_sarif_result_code_flows_location(trace_item):
    location = []
    if trace_item[0] == "CliLoc":
        location.append(parse_loc_cliloc(trace_item))
    elif 'content' in trace_item[0]:
        location.append(parse_loc_content(trace_item))
    elif trace_item[0] == "CliCall":
        # this needs to get recursive for the trace_item[1+] items
        for item in trace_item[1]:
            if isinstance(item, list) and not isinstance(item[-1],str) and not isinstance(item[0],str):
                for sub_item in item:
                    location += build_sarif_result_code_flows_location([sub_item])
            else:
                location += build_sarif_result_code_flows_location(item)
    else:
        location.append(parse_loc_no_label(trace_item))

    return location

def build_sarif_result_code_flows_locations(finding):
    locations = []

    trace_keys = ['taint_source', 'intermediate_vars', 'taint_sink']
    for key in trace_keys:
        if key in finding['extra']['dataflow_trace']:
            locations += build_sarif_result_code_flows_location(finding['extra']['dataflow_trace'][key])
    
    return locations

def build_sarif_result_code_flows(finding):
    code_flows = []

    if 'dataflow_trace' in finding['extra']:
        code_flows = [{
        "threadFlows": [{
            "locations": build_sarif_result_code_flows_locations(finding)
        }]
    }]

    return code_flows

def finding_to_sarif_result(finding):
    return {
        "codeFlows": build_sarif_result_code_flows(finding),
        "fingerprints": {
            "matchBasedId/v1": finding['extra']['fingerprint']
        },
        "locations": build_sarif_result_locations(finding),
        "message": {
            "text": finding['extra']['message'],
        },
        "properties": {},
        "ruleId": finding['check_id']
    }

def finding_to_help_markdown_references(finding):
    references = ""
    references += f"\n - [Semgrep Rule]({finding['extra']['metadata']['source']})"
    if 'references' in finding['extra']['metadata']:
        for ref in finding['extra']['metadata']['references']:
            references += f"\n - [{ref}]({ref})"
    return f"{references}\n"

def finding_to_driver_rule_help_markdown(finding):
    markdown = finding['extra']['message']
    markdown += "\n\n<b>References:</b>"
    markdown += finding_to_help_markdown_references(finding)
    return markdown

def severity_to_level(severity):
    severity_mapping = {
        'info': 'note',
        'warning': 'warning',
        'error': 'error'
    }
    return severity_mapping[severity.lower()]

def finding_to_driver_rule_properties_tags(finding):
    tags = []
    if 'cwe' in finding['extra']['metadata']:
        if isinstance(finding['extra']['metadata']['cwe'], list):
            tags.extend(finding['extra']['metadata']['cwe'])
        else:
            tags.append(finding['extra']['metadata']['cwe'])
    if 'owasp' in finding['extra']['metadata']:
        if isinstance(finding['extra']['metadata']['owasp'], list):
            tags.extend(finding['extra']['metadata']['owasp'])
        else:
            tags.append(finding['extra']['metadata']['owasp'])
    if 'confidence' in finding['extra']['metadata']:
        tags.append(f"{finding['extra']['metadata']['confidence']} confidence")
    if 'category' in finding['extra']['metadata']:
        tags.append(finding['extra']['metadata']['category'])
    return tags

def finding_to_precision(finding):
    precision_mapping = {
        'low': 'medium',
        'medium': 'high',
        'high': 'very-high'
    }
    return precision_mapping.get(finding['extra']['metadata'].get('confidence', '').lower(), 'high')

def finding_to_security_severity(finding):
    severity_mapping = {
        'info': '3.0',
        'warning': '6.0',
        'error': '8.0'
    }
    return severity_mapping[finding['extra']['severity'].lower()]

def finding_to_cwe_brief(finding):
    if (finding['extra']['metadata'].get('cwe','') == ''):
        return ''
    elif (isinstance(finding['extra']['metadata']['cwe'], list)):
        return finding['extra']['metadata']['cwe'][0].split(': ')[1]
    else:
        return finding['extra']['metadata']['cwe'].split(': ')[1]

def finding_to_short_description(finding):
    if (finding['check_id'].startswith('ssc')):
        # do ssc short desc
        cwe_brief = finding_to_cwe_brief(finding)
        package = finding['extra']['sca_info']['dependency_match']['dependency_pattern']['package']
        semver_range = finding['extra']['sca_info']['dependency_match']['dependency_pattern']['semver_range']

        return f"[Semgrep Supply Chain] {cwe_brief} in {package} ({semver_range})"
    elif (finding['extra']['metadata'].get('product','')=='secrets'):
        cwe_brief = finding_to_cwe_brief(finding)
        rule_id_brief = finding['check_id'].split('.')[-1]
        return f"[Semgrep Secrets] {cwe_brief}: '{rule_id_brief}'"
    else:
        cwe_brief = finding_to_cwe_brief(finding)
        rule_id_brief = finding['check_id'].split('.')[-1]
        return f"[Semgrep Code] {cwe_brief}: '{rule_id_brief}'"

def finding_to_driver_rule(finding):
    return {
        "defaultConfiguration": {
            "level": severity_to_level(finding['extra']['severity']),
        },
        "fullDescription": {
            "text": finding['extra']['message']
        },
        "help": {
            "markdown": finding_to_driver_rule_help_markdown(finding),
            "text": finding['extra']['message']
        },
        "helpUri": finding['extra']['metadata']['source'],
        "id": finding['check_id'],
        "name": finding['check_id'],
        "properties": {
            "precision": finding_to_precision(finding), 
            "tags": finding_to_driver_rule_properties_tags(finding),
            "security-severity": finding_to_security_severity(finding)
        },
        "shortDescription": {
            "text": f"{finding_to_short_description(finding)}" # todo make better short description
        }
    }

def build_sarif_runs_invocations(findings):
    return [{
        "executionSuccessful": True,
        "toolExecutionNotifications": []
    }]

def build_sarif_runs_results(findings):
    return [finding_to_sarif_result(f) for f in findings['results']]

def get_rules_from_findings(findings):
    rules = [f['check_id'] for f in findings]
    return list(set(rules))


def get_first_finding_per_rule(findings):
    rules = get_rules_from_findings(findings)
    unique_findings = []
    for rule in rules:
        for finding in findings:
            if finding['check_id'] == rule:
                unique_findings.append(finding)
                break
    return unique_findings

def build_sarif_runs_tool_driver_rules(findings):
    example_findings = get_first_finding_per_rule(findings)
    return [finding_to_driver_rule(f) for f in example_findings]

def build_sarif_runs_tool(findings):
    return {
        'driver': {
            'name': "Semgrep Pro",
            'rules': build_sarif_runs_tool_driver_rules(findings['results']),
            'semanticVersion': findings['version']
        }
    }

def build_sarif_runs(findings):
    return [{
        'invocations': build_sarif_runs_invocations(findings),
        'results': build_sarif_runs_results(findings),
        'tool': build_sarif_runs_tool(findings)
    }]

def build_sarif_template():
    return {
        "$schema": "https://docs.oasis-open.org/sarif/sarif/v2.1.0/os/schemas/sarif-schema-2.1.0.json",
        "runs": [],
        "version": "2.1.0"
    }

def write_sarif_file(data, output_file):
    sarif_string = json.dumps(data, indent=4)
    with open(output_file, 'w') as f:
        f.write(sarif_string)

def include_in_sarif(finding):
    if (finding['check_id'].startswith('ssc')):
        return finding['extra']['sca_info']['reachable'] # if ssc reachable
    else:
        return ('monitor' not in finding['extra']['metadata']['dev.semgrep.actions']) # code or secrets finding configured to comment / block

def filter_findings_results(findings):
    # Only post rules in comment and block
    filtered_results = [r for r in findings['results'] if include_in_sarif(r)]
    return filtered_results

def load_findings(findings_file):
    with open(findings_file) as f:
        return json.load(f)

def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(description='Generate a SARIF report from Semgrep\'s JSON output.')
    # Add arguments for SARIF file and output file name
    parser.add_argument('-j', '--json', default='semgrep.json', help='Input Semgrep findings json file. Default is semgrep.json.')
    parser.add_argument('-s', '--sarif', default='semgrep.sarif', help='Output sarif file name. Default is semgrep.sarif.')

    # Parse the command-line arguments
    args = parser.parse_args()
    print(f"\nTransforming Semgrep JSON {args.json} to SARIF {args.sarif}... ")

    # Load findings from the specified file
    findings = load_findings(args.json)
    # findings['results'] = filter_findings_results(findings)
    sarif = build_sarif_template()
    sarif['runs'] = build_sarif_runs(findings)

    write_sarif_file(sarif, args.sarif)
    
    print(f"{args.sarif} written.  {args.json} transform complete.")

if __name__ == '__main__':
    main()
