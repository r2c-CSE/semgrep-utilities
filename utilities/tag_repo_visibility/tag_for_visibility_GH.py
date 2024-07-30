import requests
import json
from dotenv import dotenv_values

# # Before running this script you will need to add a .env file to the same folder. The .env file should contian the following values:
# # GitHub personal access token with permission to read the metadata for all the repos.
# GITHUB_TOKEN = 'your_github_token'
# # GitHub organization
# GITHUB_ORG = 'your_org'
# # GitHub API base URL. No need to alter this value.
# GITHUB_API_URL = 'https://api.github.com'
# # Semgrep Organization Slug (Found by going to the Semgrep settings and scrolling to the bottom).
# SEMGREP_ORG_SLUG = 'your_semgrep_org_slug'
# # Semgrep API token. Acquired from the Semgrep 'Settings -> Tokens' page.
# SEMGREP_API_TOKEN='your_semgrep_api_token'

#Fetch all repositories from GITHUB_ORG.
def get_repositories(github_org_name, api_token, base_url):
    headers = {
        'Authorization': f'token {api_token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    repos = []
    page = 1
    
    while True:
        response = requests.get(
            f'{base_url}/orgs/{github_org_name}/repos',
            headers=headers,
            params={'page': page, 'per_page': 100}
        )
        if response.status_code != 200:
            raise Exception(f'Error fetching repositories: {response.status_code}')
        
        data = response.json()
        if not data:
            break
        
        repos.extend(data)
        page += 1
    
    return repos

#Add tag to project in Semgrep. 
def add_tag(api_token, org_slug, project_name, tag):
    payload = {
        "tags": [
            tag
        ]
    }
    
    response = requests.put(
        'https://semgrep.dev/api/v1/deployments/' + org_slug + '/projects/' + project_name + '/tags',
        data=json.dumps(payload),
        headers={
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json'
        }
    )
    
    if response.status_code != 200:
        print(f'Failed to post visibility for repo {project_name}: {response.status_code}')
    else:
        print(f'Successfully posted visibility for repo {project_name}')

#Fetch all repositories from GitHub org. Tag the corresponding projects in Semgrep with the repository's visibility: public, private, or internal. 
def main():
    config = dotenv_values(".env")

    repos = get_repositories(config['GITHUB_ORG'], config['GITHUB_API_TOKEN'], config['GITHUB_API_URL'])
    
    for repo in repos:
        repo_name = repo['name']
        visibility = repo['visibility']
        project_name = config['GITHUB_ORG'] + '/' + repo_name
        add_tag(config['SEMGREP_API_TOKEN'], config['SEMGREP_ORG_SLUG'], project_name, visibility)

if __name__ == '__main__':
    main()
