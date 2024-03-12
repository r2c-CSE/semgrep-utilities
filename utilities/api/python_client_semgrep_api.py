import requests
import sys
import json
import re
import os


def get_deployments():
    headers = {"Accept": "application/json", "Authorization": "Bearer " + SEMGREP_APP_TOKEN}

    r = requests.get('https://semgrep.dev/api/v1/deployments',headers=headers)
    if r.status_code != 200:
        sys.exit(f'Get failed: {r.text}')
    data = json.loads(r.text)
    slug_name = data['deployments'][0].get('slug')
    print("Accessing org: " + slug_name)
    return slug_name

def get_projects(slug_name):
    
    headers = {"Accept": "application/json", "Authorization": "Bearer " + SEMGREP_APP_TOKEN}

    r = requests.get('https://semgrep.dev/api/v1/deployments/' + slug_name + '/projects',headers=headers)
    if r.status_code != 200:
        sys.exit(f'Get failed: {r.text}')
    data = json.loads(r.text)
    for project in data['projects']:
        project_name = project['name']
        print("Getting findings for: " + project_name)
        get_findings_per_repo(slug_name, project_name)


def get_findings_per_repo(slug_name, repo):
    headers = {"Accept": "application/json", "Authorization": "Bearer " + SEMGREP_APP_TOKEN}
    r = requests.get('https://semgrep.dev/api/v1/deployments/' + slug_name + '/findings?repos='+repo+'&dedup=true',headers=headers)
    if r.status_code != 200:
        sys.exit(f'Get failed: {r.text}')
    data = json.loads(r.text)
    file_path = re.sub(r"[^\w\s]", "", repo) + ".json"
    with open(file_path, "w") as file:
         json.dump(data, file)

if __name__ == "__main__":
    try:  
        SEMGREP_APP_TOKEN = os.getenv("SEMGREP_APP_TOKEN") 
    except KeyError: 
        print("Please set the environment variable SEMGREP_APP_TOKEN") 
        sys.exit(1)
    slug_name = get_deployments()
    get_projects(slug_name)
    ##get_findings_per_repo(slug_name,"local_scan/api_check")
    ## add whatever method you want to try
