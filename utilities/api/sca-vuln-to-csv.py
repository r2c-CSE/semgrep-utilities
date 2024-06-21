import requests
import sys
import json
import re
import os
import pandas as pd

BASE_URL = 'https://semgrep.dev/api/v1/deployments'

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
        print("Getting findings for: " + project_name)
        get_findings_per_project(deployment_slug, project_name, headers)
    

def get_findings_per_project(deployment_slug, project, headers):
    """
    Gets all findings for a project, and writes them to a file.
    The file format is equivalent to what the API would return if it weren't paginated.
    """
    project_findings = retrieve_paginated_data(f"{BASE_URL}/{deployment_slug}/findings?repos={project}&dedup=true&issue_type=sca", "findings", 3000, headers=headers)
    file_path = re.sub(r"[^\w\s]", "-", project) + ".json"
    with open(file_path, "w") as file:
         file.write(project_findings)


def combine_json_files(folder_path, output_file):
    combined_data = []
   
    # Loop through each file in the folder
    total_findings = 0
    for filename in os.listdir(folder_path):
        if filename.endswith('.json'):
            print("Opening " + filename)
            if filename != "combined.json":
                print("Opening file with filename: " + filename)
                with open(os.path.join(folder_path, filename), 'r') as file:
                    data = json.load(file)
                    total_findings = total_findings + len(data['findings'])
                    if len(data['findings']) > 0:
                        # Append data from current file to combined data
                        if isinstance(data, list):
                            combined_data.extend(data['findings'])
                        else:
                            combined_data.append(data['findings'])
                # delete the JSON file after reading its contents
                try:
                    os.remove(filename)
                    print(f"Deleted: {filename}")
                except OSError as e:
                    print(f"Error: {e.strerror} - {filename}")                    
            else:
                print("Skipped file with filename: "+filename)
    print(total_findings)
 
    # Write combined data to output file
    with open(output_file, 'w') as outfile:
        json.dump(combined_data, outfile, indent=4)
 
def json_to_df(json_file):
   with open(os.path.join(".", json_file), 'r') as file:
        data = json.load(file)

        # Flatten the JSON structure
        flattened_data = [item for sublist in data for item in sublist]

        # Convert to DataFrame
        df = pd.json_normalize(flattened_data)

        return df
 
def json_to_csv_pandas(json_file, csv_file):
 
    df = json_to_df(json_file)
    # Write the DataFrame to CSV
    df.to_csv(csv_file, index=False)

def add_repo_details(row):
    return (row['repository']['name'])


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
    combine_json_files('.', 'combined.json')
    print ("completed combine process")
    print ("starting process to convert combined JSON file to csv & xlsx")
    json_to_csv_pandas('combined.json', 'output.csv')
    print ("completed conversion process")
