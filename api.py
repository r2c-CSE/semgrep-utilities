import requests
import sys

SEMGREP_APP_TOKEN = "xxxxxxxx"

def get_deployments():
    headers = {"Accept": "application/json", "Authorization": "Bearer " + SEMGREP_APP_TOKEN}

    r = requests.get('https://semgrep.dev/api/v1/deployments',headers=headers)
    if r.status_code != 200:
        sys.exit(f'Get failed: {r.text}')
    print(r.text)


def get_findings_per_repo():
    
    repo = 'r2c-CSE/test-semgrep-pro'

    headers = {"Accept": "application/json", "Authorization": "Bearer " + SEMGREP_APP_TOKEN}

    r = requests.get('https://semgrep.dev/api/v1/deployments/r2c_cse/findings?repos='+repo,headers=headers)
    if r.status_code != 200:
        sys.exit(f'Get failed: {r.text}')
    print(r.text)




if __name__ == "__main__":

    get_findings_per_repo()