import requests
import sys
import json
import os
import logging
from pathlib import Path

BASE_URL = 'https://semgrep.dev/api/v1/deployments'

def get_deployment_id(headers):
    r = requests.get(f"{BASE_URL}",headers=headers)
    if r.status_code != 200:
        sys.exit(f'Could not get deployment: {r.status_code} {r.text}')
    org_id = str(r.json()['deployments'][0].get('id'))
    logging.info("Accessing org: " + org_id)
    return org_id

def get_deployment_slug_name(headers):
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
    logging.info("Accessing org: " + deployment_slug)
    return deployment_slug

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
        payload = {"pageSize": page_size, "page": page}
        page_string = ""
        if (kind == 'projects'):
            page_string = f"?page_size={page_size}&page={page}"
            r = requests.get(f"{endpoint}{page_string}", headers=headers)
        else:
            r = requests.post(f"{endpoint}", headers=headers, json=payload)
        if r.status_code != 200:
            sys.exit(f'Get failed: {r.text}')
        data = r.json()
        if (kind == 'projects'):
            if not data.get(kind):
                logging.info(f"At page {page} there is no more data of {kind}")
                hasMore = False
        else:
            hasMore = data['hasMore']
        data_list.extend(data.get(kind))

    return json.dumps({ f"{kind}": data_list})

def get_projects(deployment_slug, headers):
    projects = retrieve_paginated_data(f"{BASE_URL}/{deployment_slug}/projects", "projects", 200, headers=headers)
    return projects

def get_repo_with_dependencies(org_id, headers):
    projects = retrieve_paginated_data(f"{BASE_URL}/{org_id}/dependencies/repositories", "repositorySummaries", 100, headers=headers)
    return projects

def diff_df(repos_with_dependencies, total_repos):
    # Extracting IDs from the first JSON object
    first_ids = {item['id'] for item in repos_with_dependencies['repositorySummaries']}

    # Filtering out items from the second JSON object that are not in the first JSON object
    filtered_projects = [project for project in total_repos['projects'] if project['id'] not in first_ids]
    result = {"projects": filtered_projects}
    return result

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
            logging.info("No Semgrep settings found")

    if token is None or token == "":
        logging.info("No token found - set the environment variable SEMGREP_APP_TOKEN or use `semgrep login` before running.")
        sys.exit(1)

    headers = {"Accept": "application/json", "Authorization": "Bearer " + token}
    logging.info("Getting ORG ID")
    org_id = get_deployment_id(headers)
    logging.info("Getting slug name")
    slug_name = get_deployment_slug_name(headers)

    logging.info("Getting Repos with dependencies")
    repos_with_dependencies = get_repo_with_dependencies(org_id, headers)
    data_repos_with_dependencies = json.loads(repos_with_dependencies)
    with open("repos_with_dependencies.json", "w") as file:
         json.dump(data_repos_with_dependencies, file)

    logging.info("Getting all projects")
    total_repos = get_projects(slug_name, headers)
    data_total_repos = json.loads(total_repos)

    logging.info("Getting projects without dependencies")
    repos_without_dependencies = diff_df(data_repos_with_dependencies, data_total_repos)
    with open("repos_without_dependencies.json", "w") as file:
         json.dump(repos_without_dependencies, file)