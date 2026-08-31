import requests
import json
from urllib.parse import quote
from dotenv import dotenv_values

# # Before running this script you will need to add a .env file to the same folder. The .env file should contian the following values:
# # GitLab personal access token with permission to read the metadata for all the projects (read_api scope).
# GITLAB_TOKEN = 'your_gitlab_token'
# # GitLab group (organization) path or ID.
# GITLAB_GROUP = 'your_group'
# # GitLab API base URL. Change this if you use a self-managed GitLab instance.
# GITLAB_API_URL = 'https://gitlab.com/api/v4'
# # Semgrep Organization Slug (Found by going to the Semgrep settings and scrolling to the bottom).
# SEMGREP_ORG_SLUG = 'your_semgrep_org_slug'
# # Semgrep API token. Acquired from the Semgrep 'Settings -> Tokens' page.
# SEMGREP_API_TOKEN='your_semgrep_api_token'

#Fetch all projects from GITLAB_GROUP, including those in subgroups.
def get_projects(gitlab_group, api_token, base_url):
    headers = {
        'PRIVATE-TOKEN': api_token
    }

    group_id = quote(gitlab_group, safe='')
    projects = []
    page = 1

    while True:
        response = requests.get(
            f'{base_url}/groups/{group_id}/projects',
            headers=headers,
            params={'page': page, 'per_page': 100, 'include_subgroups': True}
        )
        if response.status_code != 200:
            raise Exception(f'Error fetching projects: {response.status_code}')

        data = response.json()
        if not data:
            break

        projects.extend(data)
        page += 1

    return projects

#Fetch the language breakdown for a single GitLab project (e.g. {"Java": 55.6, "Ruby": 30.2}).
def get_languages(project_id, api_token, base_url):
    headers = {
        'PRIVATE-TOKEN': api_token
    }

    response = requests.get(f'{base_url}/projects/{project_id}/languages', headers=headers)
    if response.status_code != 200:
        raise Exception(f'Error fetching languages for project {project_id}: {response.status_code}')

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

#Fetch all projects from a GitLab group. Tag the corresponding projects in Semgrep with the project's
#visibility, topics, and source code languages.
def main():
    config = dotenv_values(".env")

    projects = get_projects(config['GITLAB_GROUP'], config['GITLAB_TOKEN'], config['GITLAB_API_URL'])

    for project in projects:
        project_name = project['path_with_namespace']
        languages = get_languages(project['id'], config['GITLAB_TOKEN'], config['GITLAB_API_URL'])

        tags = [project['visibility']]
        tags += [f'topic:{topic}' for topic in project.get('topics', [])]
        tags += [f'language:{language}' for language in languages]

        add_tags(config['SEMGREP_API_TOKEN'], config['SEMGREP_ORG_SLUG'], project_name, tags)

if __name__ == '__main__':
    main()
