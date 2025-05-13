import requests
import sys
import json
import os
from pathlib import Path

def get_deployment_id():
    headers = {"Accept": "application/json", "Authorization": "Bearer " + token}
    r = requests.get('https://semgrep.dev/api/v1/deployments',headers=headers)
    if r.status_code != 200:
        sys.exit(f'Could not get deployment: {r.status_code} {r.text}')
    org_id = str(r.json()['deployments'][0].get('id'))
    print("Accessing org: " + org_id)
    return org_id

def get_sca_dependencies(org_id):
    dependencies = []
    file_path = "dependencies.json"

    headers = {"Accept": "application/json", "Authorization": "Bearer " + token}
    payload = {"pageSize": 100}
    has_more = True

    while (has_more == True):
        print(f"Making request with payload {payload}")
        r = requests.post(f"https://semgrep.dev/api/v1/deployments/{org_id}/dependencies",headers=headers, json=payload)
        if r.status_code != 200:
            sys.exit(f'Could not get dependencies: {r.status_code} {r.text}')
        data = r.json()
        dependencies += data['dependencies']
        payload['cursor'] = data['cursor']
        has_more = data['hasMore']
    with open(file_path, "w") as file:
        json.dump(dependencies, file)


if __name__ == "__main__":
    token = os.getenv("SEMGREP_APP_TOKEN")
    if token is None:
        # Look for the .semgrep/settings.yml where we keep login tokens if no ENV var
        try:
            semgrep_settings = open(Path.home() / ".semgrep" / "settings.yml", "r")
            lines = semgrep_settings.readlines()
            # the line we want starts with api_token
            token_line = [line.rstrip() for line in lines if line.startswith("api_token")].pop()
            _, token = token_line.split(': ')
            semgrep_settings.close()
        except FileNotFoundError:
            print("No Semgrep settings found")

    if token is None or token == "":
        print("No token found - set the environment variable SEMGREP_APP_TOKEN or use `semgrep login` before running.")
        sys.exit(1)

    org_id = get_deployment_id()
    get_sca_dependencies(org_id)