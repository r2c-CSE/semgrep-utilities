import os
import json
import sys
import argparse

from jira import JIRA
import config

jira = JIRA(
    server=config.JIRA_SERVER, 
    token_auth=os.environ.get(config.JIRA_TOKEN_ENV_VAR)
)

def handle_findings_batched(findings, action="query"):
    batch_size = 25
    batches = [findings[i:i + batch_size] for i in range(0, len(findings), batch_size)]
    issues = []

    print(f'\n{len(findings)} findings to {action} in batches of {batch_size}...')

    for i, batch in enumerate(batches):
        print(f'\nHandling batch {i+1}/{len(batches)}...')
        if action == "query":
            issues.extend(query_issues(batch))
        elif action == "create":
            issues.extend(create_issues(batch))
        else:
            print(f"Invalid action: {action}. Quitting to avoid other issues. Exiting code 0 to avoid CI/CD failure.")
            sys.exit(0)

    return issues

def create_issues(findings):
    print(f'Creating {len(findings)} issues...')
    issues_data = list(map(config.finding_to_issue, findings))

    try:
        issues = jira.create_issues(field_list=issues_data)
    except Exception as e:
        print(f"Error creating issues: {str(e)}")
        issues = []

    for issue in issues:
        if issue['status']=='Error':
            print(f"Error creating issue: {issue['error']} for fingerprint {issue['input_fields'][config.JIRA_FINGERPRINT_FIELD]}")
            continue

        _issue = issue['issue']
        print(f"Created issue: [ {_issue.key} ] for fingerprint: {_issue.get_field(config.JIRA_FINGERPRINT_FIELD)}")

    return issues

def query_issues(findings): 
    print(f'Querying Jira for {len(findings)} findings...')
    fingerprints = [finding['extra']['fingerprint'] for finding in findings]
    jql = f"project={config.JIRA_PROJECT} and cf[{config.JIRA_FINGERPRINT_FIELD_ID}] ~ \"({' OR '.join(fingerprints)})\""

    try:
        issues = jira.search_issues(jql)
    except Exception as e:
        print(f"Error querying issues: {str(e)}")
        print("\nQuitting to avoid creating duplicate issues. Exiting code 0 to avoid CI/CD failure.")
        sys.exit(0)

    for issue in issues:
        print(f"Found existing issue: [ {issue.key} ] for fingerprint: {issue.get_field(config.JIRA_FINGERPRINT_FIELD)}")

    return issues

def get_findings_without_issues(findings, issues):
    issue_fingerprints = [issue.get_field(config.JIRA_FINGERPRINT_FIELD) for issue in issues]
    return [finding for finding in findings if finding['extra']['fingerprint'] not in issue_fingerprints]

def parse_arguments():
    parser = argparse.ArgumentParser(description='Sync Semgrep findings to Jira.')
    parser.add_argument('-f', '--findings-file', required=True, help='Path to the Semgrep findings JSON file.')
    args = parser.parse_args()
    return args

def log_start():
    print('\n┌─────────────────────────────────────┐')
    print('\n│ Syncing Semgrep findings to Jira... │')
    print('\n└─────────────────────────────────────┘')

def main():
    log_start()

    try:
        args = parse_arguments()
        semgrep_findings_file_path = args.findings_file

        with open(semgrep_findings_file_path, 'r') as f:
            findings = json.load(f)['results']

        issuable_findings = config.filter_findings(findings)
        print(f"\nSyncing {len(issuable_findings)}/{len(findings)} findings to Jira...")
        existing_issues = handle_findings_batched(issuable_findings, action="query")
        findings_without_issues = get_findings_without_issues(issuable_findings, existing_issues)
        new_issues = handle_findings_batched(findings_without_issues, action="create")

        print('\nDone.\n')
    except Exception as e:
        print(f"An error occurred: {str(e)}. Exiting code 0 to avoid CI/CD failure.")
        sys.exit(0)

if __name__ == "__main__":
    main()
