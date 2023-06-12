import requests
import sys

SEMGREP_APP_TOKEN = "XXXXX"

repo = 'r2c-CSE/test-semgrep-pro'
slug_name = "r2c_cse"
org_id = "8849"

def get_deployments():
    headers = {"Accept": "application/json", "Authorization": "Bearer " + SEMGREP_APP_TOKEN}

    r = requests.get('https://semgrep.dev/api/agent/deployments',headers=headers)
    if r.status_code != 200:
        sys.exit(f'Get failed: {r.text}')
    print(r.text)


def get_projects():
    
    headers = {"Accept": "application/json", "Authorization": "Bearer " + SEMGREP_APP_TOKEN}

    r = requests.get('https://semgrep.dev/api/v1/deployments/' + slug_name + '/projects?page=0',headers=headers)
    if r.status_code != 200:
        sys.exit(f'Get failed: {r.text}')
    print(r.text)


def get_projects_internal_api():
    
    headers = {"Accept": "application/json", "Authorization": "Bearer " + SEMGREP_APP_TOKEN}

    r = requests.get('https://semgrep.dev/api/agent/deployments/' + org_id + '/repos?page=0',headers=headers)
    if r.status_code != 200:
        sys.exit(f'Get failed: {r.text}')
    print(r.text)


def get_findings_per_repo():
      
    headers = {"Accept": "application/json", "Authorization": "Bearer " + SEMGREP_APP_TOKEN}

    r = requests.get('https://semgrep.dev/api/v1/deployments/' + slug_name + '/findings?repos='+repo,headers=headers)
    if r.status_code != 200:
        sys.exit(f'Get failed: {r.text}')
    print(r.text)


if __name__ == "__main__":
    get_deployments()
    get_projects()
    get_projects_internal_api()
    get_findings_per_repo()