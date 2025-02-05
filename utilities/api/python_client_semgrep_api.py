import json
import os
import re
import requests
import sys

BASE_URL = 'https://semgrep.dev/api/v1/deployments'
USE_PRIMARY_BRANCH_PARAM = True

def retrieve_paginated_data(endpoint, kind, page_size, headers):
    """
    Generalized function to retrieve multiple pages of data.
    Returns all data as a JSON string (not a Python dict!) in the same format 
    as the API would if it weren't paginated.
    """
    # Initialize values
    data_list = []
    hasMore = True
    page = -1
    while (hasMore == True):
        page = page + 1
        page_string = ""
        if (kind == 'projects'):
            page_string = f"?page_size={page_size}&page={page}"
        else:
            page_string = f"&page_size={page_size}&page={page}"
        r = requests.get(f"{endpoint}{page_string}", headers=headers)
        if r.status_code != 200:
            sys.exit(f'Get failed: {r.text}')
        data = r.json()
        if not data.get(kind):
            hasMore = False
        data_list.extend(data.get(kind))
    return json.dumps({ f"{kind}": data_list})

def get_deployment(headers):
    """
    Gets the deployment slug for use in other API calls.
    API tokens are currently per-deployment, so there's no need to 
    iterate or paginate.
    """
    r = requests.get(BASE_URL, headers=headers)
    if r.status_code != 200:
        sys.exit(f'Get failed: {r.text}')
    data = r.json()

    deployment_slug = data['deployments'][0].get('slug')
    print("Accessing org: " + deployment_slug)
    return deployment_slug


def get_projects(deployment_slug, headers):
    """
    Gets the list of projects for use in other API calls.
    This call must paginate to work for users with larger numbers of projects.
    """
    projects = retrieve_paginated_data(f"{BASE_URL}/{deployment_slug}/projects", "projects", 200, headers=headers)
    return projects
    
def get_all_findings(projects, headers):
    """
    Gets all findings for all projects.
    """
    for project in projects['projects']:
        project_name = project['name']
        primary_branch = project['primary_branch']
        primary_branch = primary_branch.replace("refs/heads/", "") # To get master (main) instead of refs/heads/master (refs/heads/main)
        print("Getting findings for: " + project_name)
        get_findings_per_project(deployment_slug, project_name, primary_branch, headers)    

def get_findings_per_project(deployment_slug, project, primary_branch, headers):
    """
    Gets all findings for a project, and writes them to a file.
    The file format is equivalent to what the API would return if it weren't paginated.
    By default, all the statutes are retrieved, but you can remove the unneeded statutes. 
    For example, if you want to retrieve open findings, then "open", "fixing", and "reviewing" statutes should be used.
    Note: &status=open,fixing or &status=open|fixing or doesn't work. 
    """
    ## all_statutes = ["open", "fixing", "reviewing", "fixed", "ignored"]
    open_statuses = ["open", "fixing", "reviewing"]
    merged_findings = {"findings": []}
    for status in open_statuses:
        findings_url = f"{BASE_URL}/{deployment_slug}/findings?repos={project}&dedup=false&status={status}"
        if USE_PRIMARY_BRANCH_PARAM:
            findings_url = f"{findings_url}&ref={primary_branch}"
        project_findings = retrieve_paginated_data(findings_url, "findings", 3000, headers=headers)
        merged_results = json.loads(project_findings)
        merged_findings["findings"].extend(merged_results.get("findings", []))

    json_merged_findings = json.dumps(merged_findings)
    file_path = re.sub(r"[^\w\s]", "-", project) + ".json"
    with open(file_path, "w") as file:
         file.write(json_merged_findings)


if __name__ == "__main__":
    try:  
        SEMGREP_APP_TOKEN = os.getenv("SEMGREP_APP_TOKEN") 
    except KeyError: 
        print("Please set the environment variable SEMGREP_APP_TOKEN") 
        sys.exit(1)
    default_headers = {"Accept": "application/json", "Authorization": "Bearer " + SEMGREP_APP_TOKEN}
    deployment_slug = get_deployment(default_headers)
    projects = get_projects(deployment_slug, default_headers) 
    # Comment this line out if you don't want all projects
    get_all_findings(json.loads(projects), default_headers)
    # Uncomment the following line and add a project name to generate a JSON file for a single project
    # get_findings_per_project(deployment_slug, "juice-shop", default_headers) 
