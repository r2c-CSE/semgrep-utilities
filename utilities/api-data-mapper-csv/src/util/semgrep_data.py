import json
import util.semgrep_finding as futil
import util.semgrep_rule as rutil
import csv


def map_finding_fields(findings, rules, rewriteCodeSeverityCritical=False):
    # Map each finding to a new finding based on metadata from the corresponding rule
    mapped_findings = []
    for finding in findings:
        try:
            rule = find_dict_by_key_value(rules, 'id', finding['rule_name'])
            mapped_finding = finding
            mapped_finding['severity'] = rutil.severity(rule, rewriteCodeSeverityCritical)
            mapped_finding['impact'] = rutil.impact(rule)
            mapped_finding['likelihood'] = rutil.likelihood(rule)
            mapped_finding['product'] = rutil.product(rule)
            mapped_finding['cwe'] = rutil.cwe(rule)
            mapped_finding['owasp'] = rutil.owasp(rule)
            mapped_findings.append(mapped_finding)
        except Exception as e:
            print(f'Error mapping finding {finding["id"]}: {e.__class__.__name__} {e}')

    return mapped_findings

def map_rule_fields(rules, rewriteCodeSeverityCritical=False):
    mapped_rules = []
    for rule in rules:
        try:
            mapped_rule = rule
            mapped_rule['severity'] = rutil.severity(rule, rewriteCodeSeverityCritical)
            mapped_rule['confidence'] = rutil.confidence(rule)
            mapped_rule['impact'] = rutil.impact(rule)
            mapped_rule['likelihood'] = rutil.likelihood(rule)
            mapped_rule['product'] = rutil.product(rule)
            mapped_rule['cwe'] = rutil.cwe(rule)
            mapped_rule['owasp'] = rutil.owasp(rule)
            mapped_rules.append(rule)
        except Exception as e:
            print(f'Error mapping rule {rule["id"]}: {e.__class__.__name__} {e}')
    
    return mapped_rules

def find_dict_by_key_value(lst, key, value):
    return next((item for item in lst if item.get(key) == value), None)

def write_to_json(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

def write_findings(findings, file_path='data/mapped-findings.csv'):
    print(f"Writing findings to file: {file_path}")
    with open(file_path, 'w', newline='') as f:
        headers = [
            'id',
            'product',
            'cwe',
            'owasp',
            'confidence',
            'severity',
            'impact',
            'likelihood',
            'created_at',
            'repository',
            'rule_name',
            'ai_autotriage',
            'ai_autotriage_reason',
            'ai_code_risk',
            'ai_code_tag',
            'findingPathUrl'
        ]
        
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()

        for finding in findings:
            writer.writerow({
                'id': finding['id'],
                'product': finding['product'],
                'cwe': finding['cwe'],
                'owasp': finding['owasp'],
                'confidence': finding['confidence'].capitalize(),
                'severity': finding['severity'],
                'impact': finding['impact'],
                'likelihood': finding['likelihood'],
                'created_at': finding['created_at'],
                'repository': finding['repository']['name'],
                'rule_name': finding['rule_name'],
                'ai_autotriage': finding['assistant']['autotriage']['verdict'] if (finding['assistant']['autotriage']) else '',
                'ai_autotriage_reason': finding['assistant']['autotriage']['reason'] if (finding['assistant']['autotriage']) else '',
                'ai_code_risk': finding['assistant']['component']['risk'] if (finding['assistant']['component']) else '',
                'ai_code_tag': finding['assistant']['component']['tag'] if (finding['assistant']['component']) else '',
                'findingPathUrl': finding['line_of_code_url']
            })

def write_rules(rules, file_path='data/mapped-rules.csv'):
    print(f"Writing rules to file: {file_path}")
    with open(file_path, 'w', newline='') as f:
        headers = [
            'id',
            'severity',
            'confidence',
            'impact',
            'likelihood',
            'product',
            'cwe',
            'owasp',
        ]
        
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()

        for rule in rules:
            writer.writerow({
                'id': rule['id'],
                'severity': rule['severity'],
                'confidence': rule['confidence'],
                'impact': rule['impact'], 
                'likelihood': rule['likelihood'],
                'product': rule['product'],
                'cwe': rule['cwe'],
                'owasp': rule['owasp']
            })
