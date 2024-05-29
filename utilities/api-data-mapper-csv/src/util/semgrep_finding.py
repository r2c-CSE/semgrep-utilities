"""
This a utility file that contains formatting functions for a Semgrep finding.
"""

def finding_to_issue_summary(finding, include_product_tag = False):
    cwe_brief = finding_to_cwe_brief(finding)
    id_brief = rule_id_brief(finding)
    response = ""

    if (is_sca(finding)):
        package = sca_package(finding)
        semver_range = sca_semver_range(finding)
        response = f"{cwe_brief} in {package} ({semver_range})"
        if include_product_tag:
            response =  f"[Semgrep Supply Chain] {response}"
    
    elif (is_secrets(finding)):
        if cwe_brief == '':
            response = f"{id_brief.capitalize()}"
        else:
            response = f"{id_brief.capitalize()}: {cwe_brief}"
        if include_product_tag:
            response =  f"[Semgrep Secrets] {response}"
    
    else:
        if cwe_brief == '':
            response = f"{id_brief.capitalize()}"
        else:
            response = f"{id_brief.capitalize()}: {cwe_brief}"    
        if include_product_tag:
            response =  f"[Semgrep Code] {response}"
    
    return response

def finding_to_issue_description(finding, repo):
    return (f"{message(finding)}\r\n"
            f"h3. Metadata\r\n\r\n"
            f"Severity: {severity(finding)}\r\n"
            f"Confidence: {confidence(finding)}\r\n"
            f"h3. Location\r\n\r\n"
            f"Repo: {repo['name']}\r\n" 
            f"Repo URL: {repo['url']}\r\n" 
            f"Branch: {repo['branch']}\r\n" 
            f"Path: {path(finding)}\r\n" 
            f"h3. References\r\n\r\n{finding_to_issue_description_reference_links(finding)}"
    )

##############################

def finding_to_cwe_brief(finding):
    if (finding['extra']['metadata'].get('cwe','') == ''):
        return ''
    elif (isinstance(finding['extra']['metadata']['cwe'], list)):
        return finding['extra']['metadata']['cwe'][0].split(': ')[1]
    else:
        return finding['extra']['metadata']['cwe'].split(': ')[1]

def finding_to_issue_description_reference_links(finding):
    references = ""
    references += f"\n - [Semgrep Rule|{semgrep_url(finding)}]"
    for ref in reference_links(finding):
        references += f"\n - [{ref}|{ref}]"
    return f"{references}\n"

def is_sca_reachable(finding):
    return is_sca(finding) and finding['extra']['metadata']['sca-kind'] == 'reachable'

def is_sca(finding):
    return finding['check_id'].startswith('ssc')

def is_secrets(finding):
    return finding['extra']['metadata'].get('product','') == 'secrets'

def is_secrets_validated(finding):
    return is_secrets(finding) and finding['extra']['validation_state'] == 'CONFIRMED_VALID'

def sca_package(finding):
    return finding['extra']['sca_info']['dependency_match']['dependency_pattern']['package']

def sca_semver_range(finding):
    return finding['extra']['sca_info']['dependency_match']['dependency_pattern']['semver_range']

def sca_cve(finding):
    return finding['extra']['metadata']['cve']

def semgrep_url(finding):
    if (is_sca(finding)):
        return finding['extra']['metadata']['semgrep.url']
    else:
        return finding['extra']['metadata']['semgrep.dev']["rule"]["url"]

def reference_links(finding):
    return finding['extra']['metadata'].get('references') or []

def semgrep_policy(finding):
    return finding['extra']['metadata']['dev.semgrep.actions'][0] if finding['extra']['metadata']['dev.semgrep.actions'] else None 

def confidence(finding):
    return finding['extra']['metadata'].get('confidence') or "Low"


def severity(finding):
    code_severity_mapping = {
        'info': 'Low',
        'warning': 'Medium',
        'error': 'High'
    }

    sca_severity_mapping = {
        'low': 'Low',
        'moderate': 'Medium',
        'high': 'High',
        'critical': 'Critical'
    }

    if (is_sca(finding)):
        return sca_severity_mapping[finding['extra']['metadata']['sca-severity'].lower()]
    else:
        return code_severity_mapping[finding['extra']['severity'].lower()]


def message(finding):
    return finding['extra']['message']

def start_line(finding):
    return finding['start']['line']

def start_line_col(finding):
    return finding['start']['col']

def end_line(finding):
    return finding['end']['line']

def end_line_col(finding):
    return finding['end']['col']

def path(finding):
    return f"{finding['path']}"

def fingerprint(finding):
    return finding['extra']['fingerprint']

def group_key(finding, repo):
    if is_sca(finding):
        return f"{repo['name']}/{rule_id(finding)}" # only alert 1x / repo /ssc rule
    else:
        return finding['extra']['fingerprint']

def rule_id(finding):
    return finding['check_id']

def rule_id_brief(finding):
    return rule_id(finding).split('.')[-1]