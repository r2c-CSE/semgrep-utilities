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
def get_repositories(github_org, api_token, base_url):
    headers = {
        'Authorization': f'token {api_token}',
        'Accept': 'application/vnd.github.v3+json'
    }

    repos = []
    page = 1

    while True:
        response = requests.get(
            f'{base_url}/orgs/{github_org}/repos',
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

#Fetch the language breakdown for a single GitHub repo (e.g. {"Java": 33021, "Ruby": 12045}).
def get_languages(github_org, repo_name, api_token, base_url):
    headers = {
        'Authorization': f'token {api_token}',
        'Accept': 'application/vnd.github.v3+json'
    }

    response = requests.get(f'{base_url}/repos/{github_org}/{repo_name}/languages', headers=headers)
    if response.status_code != 200:
        raise Exception(f'Error fetching languages for repo {repo_name}: {response.status_code}')

    return response.json()

#Set the full tag list for a project in Semgrep. This replaces any tags previously set by this script.
def add_tags(api_token, org_slug, project_name, tags):
    payload = {
        "tags": tags
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
        print(f'Failed to post tags for repo {project_name}: {response.status_code}')
    else:
        print(f'Successfully posted tags for repo {project_name}')

#Fetch all repositories from a GitHub org. Tag the corresponding projects in Semgrep with the repo's
#visibility, topics, and source code languages.
def main():
    config = dotenv_values(".env")

    repos = get_repositories(config['GITHUB_ORG'], config['GITHUB_TOKEN'], config['GITHUB_API_URL'])

    for repo in repos:
        repo_name = repo['name']
        project_name = config['GITHUB_ORG'] + '/' + repo_name
        languages = get_languages(config['GITHUB_ORG'], repo_name, config['GITHUB_TOKEN'], config['GITHUB_API_URL'])

        tags = [repo['visibility']]
        tags += [f'topic:{topic}' for topic in repo.get('topics', [])]
        tags += [f'language:{language}' for language in languages]

        add_tags(config['SEMGREP_API_TOKEN'], config['SEMGREP_ORG_SLUG'], project_name, tags)

if __name__ == '__main__':
    main()
