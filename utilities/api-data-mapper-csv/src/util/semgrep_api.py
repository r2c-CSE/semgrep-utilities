import json
import os
import re
import requests
import sys
import csv
from pathlib import Path

BASE_URL = 'https://semgrep.dev/api/v1'
BASE_PATH = Path(__file__).resolve().parent.parent.parent

try:  
    SEMGREP_APP_TOKEN = os.getenv("SEMGREP_APP_TOKEN") 
except KeyError: 
    print("Please set the environment variable SEMGREP_APP_TOKEN") 
    sys.exit(1)

default_headers = {
    "Accept": "application/json", 
    "Authorization": "Bearer " + SEMGREP_APP_TOKEN,
    "User-Agent": "Semgrep/1.70.0 (Docker) (command/ci)"
}

def retrieve_paginated_data(endpoint, kind, page_size):
    """
    Generalized function to retrieve multiple pages of data.
    Returns all data as a JSON string (not a Python dict!) in the same format 
    as the API would if it weren't paginated.
    """
    if ("/secrets" in endpoint):
        return {
            "findings": get_secrets_data(endpoint)
        }
    else:
        # Initialize values
        data_list = []
        hasMore = True
        page = -1
        while (hasMore == True):
            page = page + 1
            page_string = f"?page_size={page_size}&page={page}"

            r = requests.get(f"{endpoint}{page_string}", headers=default_headers)
            if r.status_code != 200:
                sys.exit(f'Get failed: {r.text}')
            data = r.json()
            if not data.get(kind):
                hasMore = False
            data_list.extend(data.get(kind))
        return { f"{kind}": data_list}

def get_secrets_data(endpoint):
    findings = []
    r = requests.get(f"{endpoint}?limit=2000", headers=default_headers)
    if r.status_code != 200:
        sys.exit(f'Get failed: {r.text}')
    else:
        data = r.json()
        findings = findings + data.get('findings')
        if (data.get('cursor')):
            findings = findings + get_secrets_data(f"{endpoint}&cursor={data.get('cursor')}")

        return findings

def get_deployment():
    """
    Gets the deployment slug for use in other API calls.
    API tokens are currently per-deployment, so there's no need to 
    iterate or paginate.
    """
    r = requests.get(f"{BASE_URL}/deployments", headers=default_headers)
    if r.status_code != 200:
        sys.exit(f'Get failed: {r.text}')
    data = r.json()
    print("Connected to deployment: " + data['deployments'][0].get('name'))
    return data['deployments'][0]
    
def get_projects(deployment):
    print("Fetching projects...")

    projects = retrieve_paginated_data(
        f"{BASE_URL}/deployments/{deployment.get('slug')}/projects", 
        "projects", 
        200
    )

    return projects['projects']
    
def get_deployment_findings(deployment):
    print("Fetching findings...")

    findings = []
    findings = findings + get_code_findings(deployment)
    findings = findings + get_secrets_findings(deployment)
    return findings

def get_code_findings(deployment):
    code_findings = retrieve_paginated_data(
        f"{BASE_URL}/deployments/{deployment['slug']}/findings", 
        "findings", 
        3000
    ).get('findings')

    return code_findings

def get_secrets_findings(deployment):
    secrets_findings = retrieve_paginated_data(
        f"{BASE_URL}/deployments/{deployment['id']}/secrets", 
        "findings", 
        3000
    ).get('findings')

    return secrets_findings

def get_ssc_findings(deployment):
    # todo
    ssc_findings = retrieve_paginated_data(
        f"{BASE_URL}/deployments/{deployment['id']}/ssc-vulns", 
        "findings", 
        3000
    ).get('findings')

    return ssc_findings
    
def get_findings_per_project(deployment, project):
    print(f"Fetching findings for project {project}...")
    findings = []
    code_findings = retrieve_paginated_data(
        f"{BASE_URL}/deployments/{deployment['slug']}/findings?repos={project}&dedup=true", 
        "findings", 
        3000
    ).get('findings')

    findings = findings + code_findings

    return findings

def get_policy():
    print("Fetching policy...")
    response = requests.post(
        "https://semgrep.dev/api/cli/scans", 
        headers=default_headers, 
        json=load_query_data(
            f"{BASE_PATH}/src/const/policy_request_payload.json"
        )
    )
    response.raise_for_status()
    data = response.json()
    return data


def load_query_data(file_path):
    with open(file_path, 'r') as json_file:
        data = json.load(json_file)
    return data

def write_to_csv(data, filename):
    print(f"Writing data to {filename}...")
    # Define the CSV file header
    fieldnames = ['id',  'severity', 'impact', 'likelihood','createdAt', 'findingPathUrl', 'repository', 'status', 'secretsValidationState', 'secretsType']
    
    # Create or open the CSV file for writing
    with open(filename, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        
        # Write the header to the CSV file
        writer.writeheader()
        
        # Iterate through each object in the data array
        for item in data:
            # Create a dictionary for the current item
            row = {
                'id': item['id'],
                'confidence': item['metadata']['confidence'] if 'confidence' in item['metadata'] else '',
                'severity': item['severity'],
                'impact': item['metadata']['impact'] if 'impact' in item['metadata'] else '',
                'likelihood': item['metadata']['likelihood'] if 'likelihood' in item['metadata'] else '',
                'createdAt': item['createdAt'],
                'findingPathUrl': item['findingPathUrl'],
                'repository': item['repository']['name'], 
                'status': item['status'],
                'secretsValidationState': item['validationState'] if 'validationState' in item else '',
                'secretsType': item['type'] if 'type' in item else ''
            }
            # Write the dictionary as a row in the CSV file
            writer.writerow(row)

def write_to_json(data, filename):
    print(f"Writing data to {filename}...")
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)


def get_findings():
    deployment = get_deployment()
    projects = get_projects(deployment) 
    findings = get_deployment_findings(deployment)
    return findings

