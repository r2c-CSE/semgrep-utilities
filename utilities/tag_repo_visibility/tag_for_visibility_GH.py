import requests
import json

# GitHub personal access token
GITHUB_TOKEN = 'your_github_token'
# GitHub organization
GITHUB_ORG = 'your_org'
# GitHub API base URL
GITHUB_API_URL = 'https://api.github.com'
#Semgrep Organization Slug (Found by going to the Semgrep settings and scrolling to the bottom).
SEMGREP_ORG_SLUG = 'your_semgrep_org_slug'
#Semgrep API token.
SEMGREP_API_TOKEN = 'your_semgrep_api_token'

#Fetch all repositories from GITHUB_ORG.
def get_repositories():
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    repos = []
    page = 1
    
    while True:
        response = requests.get(
            f'{GITHUB_API_URL}/orgs/{GITHUB_ORG}/repos',
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
def add_tag(project_name, tag):
    payload = {
        "tags": [
            tag
        ]
    }
    
    response = requests.put(
        'https://semgrep.dev/api/v1/deployments/' +  SEMGREP_ORG_SLUG + '/projects/' + project_name + '/tags',
        data=json.dumps(payload),
        headers={
            'Authorization': f'Bearer {SEMGREP_API_TOKEN}',
            'Content-Type': 'application/json'
        }
    )
    
    if response.status_code != 200:
        print(f'Failed to post visibility for repo {project_name}: {response.status_code}')
    else:
        print(f'Successfully posted visibility for repo {project_name}')

#Fetch all repositories from GitHub org. Tag the corresponding projects in Semgrep with the repository's visibility: public, private, or internal. 
def main():
    repos = get_repositories()
    
    for repo in repos:
        repo_name = repo['name']
        visibility = repo['visibility']
        project_name = GITHUB_ORG + '/' + repo_name
        add_tag(project_name, visibility)

if __name__ == '__main__':
    main()
