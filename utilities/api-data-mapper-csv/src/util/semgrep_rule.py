
def should_reclassify_critical(rule):
    return (
        rule['severity'].lower() == 'error' and
        rule['metadata']['impact'].lower() == 'high' and
        (
            rule['metadata']['likelihood'].lower() == 'high' or
            rule['metadata']['likelihood'].lower() == 'medium'
        ) and
        (
            rule['metadata']['confidence'].lower() == 'high' or
            rule['metadata']['confidence'].lower() == 'medium'
        )
    )

def is_sca(rule):
    return rule['id'].startswith('ssc-')

def is_secrets(rule):
    return rule['id'].startswith('secrets.')

def is_code(rule):
    return (not is_sca(rule)) and (not is_secrets(rule))

def severity(rule, rewrite=False):
    code_severity_mapping = {
        'info': 'Low',
        'warning': 'Medium',
        'error': 'High'
    }

    if is_sca(rule):
        return rule['metadata']['sca-severity'].capitalize()

    if (rewrite and should_reclassify_critical(rule)):
        return 'Critical'
    else:
        return code_severity_mapping[rule['severity'].lower()] 
    
def confidence(rule):
    return rule['metadata'].get('confidence').capitalize() or 'Low'

def impact(rule):
    if is_sca(rule):
        return ''
    else:
        return rule['metadata'].get('impact').capitalize() or 'Low'

def likelihood(rule):
    if is_sca(rule):
        return ''
    else:
        return rule['metadata'].get('likelihood').capitalize() or 'Low'
    
def product(rule):
    if is_sca(rule):
        return 'Supply Chain'
    elif is_secrets(rule):
        return 'Secrets'
    else:
        return 'Code'
    
def cwe(rule):
    return rule['metadata']['cwe'][0] if rule['metadata'].get('cwe') else ''

def owasp(rule):
    return rule['metadata']['owasp'][0] if rule['metadata'].get('owasp') else ''