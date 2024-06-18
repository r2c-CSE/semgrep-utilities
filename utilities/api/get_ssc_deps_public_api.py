import requests
import sys
import json
import os
import csv
from pathlib import Path

def get_deployment_id():
    headers = {"Accept": "application/json", "Authorization": "Bearer " + token}
    r = requests.get('https://semgrep.dev/api/v1/deployments',headers=headers)
    if r.status_code != 200:
        sys.exit(f'Could not get deployment: {r.status_code} {r.text}')
    org_id = str(r.json()['deployments'][0].get('id'))
    slug = str(r.json()['deployments'][0].get('slug'))
    print(f"Accessing org: {org_id}, Deployment Slug: {slug}")
    return (org_id, slug)

def get_list_of_projects(slug):
    print(f"Accessing list of projects for slug :{slug}")
    file_path = "projects.json"
    csv_file_path = "projects.csv"

    headers = {"Accept": "application/json", "Authorization": "Bearer " + token}
    params =  {"page_size": 3000}

    r = requests.get(f"https://semgrep.dev/api/v1/deployments/{slug}/projects",headers=headers, params=params)
    if r.status_code != 200:
        sys.exit(f'Could not get list of projects: {r.status_code} {r.text}')
    data = r.json()

    return (data)

def get_sca_dependencies(org_id, page_size):
    print(f"Accessing list of dependencies for org_Id :{org_id}")

    all_dependencies = []
    cursor = '0'

    data = get_sca_dependencies_per_page(org_id, cursor, page_size)
    all_dependencies.extend(data['dependencies'])
    cursor = data.get('cursor')

    while data.get('hasMore', False):
        data = get_sca_dependencies_per_page(org_id, cursor, page_size)
        all_dependencies.extend(data['dependencies'])
        cursor = data.get('cursor')
    
    return(all_dependencies)

def get_sca_dependencies_per_page(org_id, cursor, page_size):
    print(f"Accessing list of dependencies for org_Id :{org_id}")

    headers = {
        "Accept": "application/json", 
        "Authorization": "Bearer " + token
        }

    payload = {
        'cursor': cursor,
        'pageSize': page_size
        }

    r = requests.post(f"https://semgrep.dev/api/v1/deployments/{org_id}/dependencies",headers=headers, json=payload)
    if r.status_code != 200:
        sys.exit(f'Could not get dependencies: {r.status_code} {r.text}')
    data = r.json()
    return data

def write_to_json(data, file_name):
    file_path = f"{file_name}.json"

    with open(file_path, "w") as file:
         json.dump(data, file)

def write_to_csv(data, file_name):
    csv_file_path = f"{file_name}.csv"

    with open(csv_file_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Repository Name', 'Package Name', 'Version', 'Ecosystem', 'Transitivity', 'License', 'Path', 'Link'])
        for dep in data:
            package = dep.get('package', {})
            licenses = ", ".join(dep.get('licenses', []))
            definedAt = dep.get('definedAt')

            writer.writerow([
                dep.get('repositoryName'),
                package.get('name'),
                package.get('versionSpecifier'),
                dep.get('ecosystem'),
                dep.get('transitivity'),
                licenses,
                definedAt.get('path'),
                definedAt.get('url')
            ])
        
def enrich_dependencies_with_projects(dependencies, projects):
    # Convert the list of projects into a dictionary with 'id' as the key
    # for quick lookup.
    projects_dict = {str(project["id"]): project["name"] for project in projects}

    # Iterate through dependencies and add the 'project name' from projects_dict
    # if the 'repositoryId' matches an 'id' in projects_dict.
    for dependency in dependencies:
        # Convert repositoryId to string to match key type in projects_dict
        repo_id = str(dependency["repositoryId"])
        if repo_id in projects_dict:
            dependency["repositoryName"] = projects_dict[repo_id]

    return dependencies

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

    (org_id, slug) = get_deployment_id()
    dependency_data = get_sca_dependencies(org_id, 10000)
    project_data = get_list_of_projects(slug)
    dependency_data_with_repo_name = enrich_dependencies_with_projects(dependency_data, project_data['projects'])
    write_to_json(project_data, 'projects')
    write_to_json(dependency_data, 'dependencies')
    write_to_json(dependency_data_with_repo_name, 'dependencies_w_projects')
    write_to_csv(dependency_data_with_repo_name, 'dependencies_w_projects')