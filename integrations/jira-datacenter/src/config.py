import subprocess
import re
import util

############################################################################################################
# This should be where you define your JIRA configuration and any custom logic for ticket creation
############################################################################################################

JIRA_SERVER='http://jira:8080'                                      # change this to https!
JIRA_TOKEN_ENV_VAR='JIRA_TOKEN'                                     # env var that holds the jira token
JIRA_PROJECT='SCRUMSEC1'                                            # jira project key
JIRA_LABELS=['Semgrep']                                             # any labels you want included on all issues
JIRA_ISSUE_TYPE='Bug'                                               # or something custom like 'Security Issue' 
JIRA_FINGERPRINT_FIELD='customfield_10300'                          # jira text field for the semgrep fingerprint, found in the field configuration page url
JIRA_FINGERPRINT_FIELD_ID=JIRA_FINGERPRINT_FIELD.split('_')[-1]     # parses the id from the fingerprint field above

# modify this to format issues and map data fields
def finding_to_issue(finding):
    return {
        "project": {
            "key": JIRA_PROJECT
        },
        "issuetype": {
            "name": JIRA_ISSUE_TYPE
        },
        "labels": JIRA_LABELS,
        "summary": util.finding_to_issue_summary(finding),
        "description": util.finding_to_issue_description(finding, repo_info()),
        JIRA_FINGERPRINT_FIELD: util.fingerprint(finding)
    }

# modify this to control what issues create tickets
def filter_findings(findings):                                  
    return [
        finding for finding in findings if (
            util.is_sca_reachable(finding) or                   # only ticket reachable SCA findings
            util.is_secrets_validated(finding) or               # or validated secrets
            ('github.com/r2c-david' in repo_info()['url'])      # or from repos in the r2c-david gh org
            or True                                             # will always create ticket
        )
    ]



############################################################################################################
# util functions for getting repo info
############################################################################################################

def repo_info():
    git_url = get_git_origin_url()
    return {
        "name": get_repo_name_from_url(git_url),
        "url": git_url,
        "branch": get_git_branch()
    }

def get_git_origin_url():
    try:
        result = subprocess.run(["git", "remote", "get-url", "origin"], check=True, text=True, capture_output=True)
        return result.stdout.strip()  
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while trying to get the git origin URL: {e}")
        return None
    
def get_git_branch():
    try:
        result = subprocess.run(["git", "branch", "--show-current"], check=True, text=True, capture_output=True)
        return result.stdout.strip()  
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while trying to get the current git branch: {e}")
        return None

def get_repo_name_from_url(url):
    match = re.search(r'.*/([^ ]*/[^.]*)', url)
    if match:
        return match.group(1)
    else:
        return None
