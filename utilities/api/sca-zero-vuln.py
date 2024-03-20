#This is a script to help get repositories without dependecies
import os, requests, json


project_data = {}
SEMGREP_APP_TOKEN = ""
def get_projects(SEMGREP_APP_TOKEN):
    headers = {"Accept": "application/json", "Authorization": "Bearer " + SEMGREP_APP_TOKEN}

    url = f"https://semgrep.dev/api/v1/deployments/{deployment_slug}/projects" #replace deployment slug with your org slug
    
    project = requests.get(url, headers=headers)
    # print(project.text)
    data = json.loads(project.text)
    return data
    


def get_repositories_without_dependencies( SEMGREP_APP_TOKEN):
    without_dependencies = []
    headers = {"Accept": "application/json", "Authorization": "Bearer " + SEMGREP_APP_TOKEN}

    url = f"https://semgrep.dev/api/v1/deployments/{deploymentId}/dependencies/repositories" #replace with your deployment id
    repository_data = project_data["projects"]

    for index, item in enumerate(repository_data):
        # print( repository_data[index])

        repo_name = item["name"]
        repo_id = item["id"]
        repo_url = item["url"]
        payload = {
            "dependencyFilter": {
                "name": "",
                "repositoryId": [
                repo_id
                ],
                    "cursor": 0,
                    "pageSize": 100
            }
        }
        response = requests.post(url, headers=headers, json=payload)
        repository_response = json.loads(response.text)
        repository_summary = repository_response['repositorySummaries']
        if len(repository_summary) < 1:
            # without_dependencies.append(repository_response)

            without_dependencies.append({"name": repo_name, "id": repo_id, "url": repo_url})
    return without_dependencies



if __name__ == "__main__":
    
    deployment_id = 2  #replace with deployment ID
    
    try:  
         SEMGREP_APP_TOKEN = os.getenv("SEMGREP_APP_TOKEN") 
         project_data = get_projects(SEMGREP_APP_TOKEN)
    except KeyError: 
        print("Please set the environment variable SEMGREP_APP_TOKEN") 
        sys.exit(1)
    if not SEMGREP_APP_TOKEN:
        print("SEMGREP_APP_TOKEN environment variable not set.")    
    else:
        repositories = get_repositories_without_dependencies( SEMGREP_APP_TOKEN)
        output_file = "repositories_without_dependencies.json"
        with open(output_file, "w") as json_file:
                json.dump(repositories, json_file, indent=4)

        print("Repositories without dependencies: ", repositories)
        
