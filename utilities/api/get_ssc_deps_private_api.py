import requests
import sys
import json
import os

def get_deployment_id():
    headers = {"Accept": "application/json", "Authorization": "Bearer " + SEMGREP_APP_TOKEN}

    r = requests.get('https://semgrep.dev/api/v1/deployments',headers=headers)
    if r.status_code != 200:
        sys.exit(f'Get failed: {r.text}')
    data = json.loads(r.text)
    org_id = str(data['deployments'][0].get('id'))
    print("Accessing org: " + org_id)
    return org_id


def get_dependencies(org_id):

    payload = {
        "dependencyFilter":{},"pageSize": 10000
    }

    file_path = "dependencies.json"
    headers = {"Accept": "application/json", "Authorization": "Bearer " + SEMGREP_APP_TOKEN}

    r = requests.post('https://semgrep.dev/api/v1/deployments/'+ org_id +'/dependencies',headers=headers,json=payload)
    if r.status_code != 200:
        sys.exit(f'Get failed: {r.text}')
    data = json.loads(r.text)
    with open(file_path, "w") as file:
         json.dump(data, file)


if __name__ == "__main__":
    try:  
        SEMGREP_APP_TOKEN = os.getenv("SEMGREP_APP_TOKEN") 
    except KeyError: 
        print("Please set the environment variable SEMGREP_APP_TOKEN") 
        sys.exit(1)
    org_id = get_deployment_id()
    get_dependencies(org_id)
