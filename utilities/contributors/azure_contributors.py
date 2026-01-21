import requests
import csv
import datetime
from dateutil.relativedelta import relativedelta
import base64

# inputs
ORGANIZATION = 'XXXXX'
PAT = 'XXXXX'
API_VERSION = '6.0'
NUMBER_OF_DAYS = 30

# Set the base URL for Azure DevOps
base_url = f'https://dev.azure.com/{ORGANIZATION}/'


pat_token = ':{}'.format(PAT).encode('utf-8')
headers = {
    'Authorization': 'Basic {}'.format(base64.b64encode(pat_token).decode('utf-8'))
}

# Function to handle paginated API requests
def fetch_all_pages(url):
    items = []
    while url:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            break
        data = response.json()
        items.extend(data['value'])
        if 'continuationToken' in response.headers:
            continuation_token = response.headers['continuationToken']
            url = f"{url}&continuationToken={continuation_token}"
        else:
            break
    return items

# Updated functions
def get_projects():
    url = f'{base_url}_apis/projects?api-version={API_VERSION}'
    return fetch_all_pages(url)

def get_repositories(project_name):
    url = f'{base_url}{project_name}/_apis/git/repositories?api-version={API_VERSION}'
    return fetch_all_pages(url)

def get_commits(project_name, repo_id, start_date):
    url = f'{base_url}{project_name}/_apis/git/repositories/{repo_id}/commits?fromDate={start_date}&api-version={API_VERSION}'
    return fetch_all_pages(url)

# Prepare the CSV file
with open('azure_repos_contributors.csv', 'w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['Project Name', 'Repo Name', 'Contributor Name', 'email_contributor', 'Number of Commits', 'Last Commit Date'])

    # Get projects
    projects = get_projects()
    print(f"list of projects: {projects}")

    # Get start date
    start_date = datetime.datetime.now() - relativedelta(days=NUMBER_OF_DAYS)


    # Updated logic for processing repositories and commits
    for project in projects:
        project_name = project['name']
        repositories = get_repositories(project_name)
        print(f"list of repos in project: {project_name} -- {repositories}")

        for repo in repositories:
            print(f"calculating contributor count for project: {project_name} -- repo: {repo['id']}")
            commits = get_commits(project_name, repo['id'], start_date)


            contributor_commits = {}
            for commit in commits:
                author = commit['author']['name']
                email_contributor = commit['author']['email']
                date = commit['committer']['date']
                # Aggregate commits by author
                if author not in contributor_commits:
                    contributor_commits[author] = {'commits': 0, 'last_commit_date': '', 'email_contributor': '' }
                contributor_commits[author]['commits'] += 1
                contributor_commits[author]['last_commit_date'] = max(contributor_commits[author]['last_commit_date'], date)
                contributor_commits[author]['email_contributor'] = email_contributor
            print(f"{project_name} , {repo['id']}-{contributor_commits}")
            for author, data in contributor_commits.items():
                # Write to CSV
                writer.writerow([project_name, repo['name'], author,  data['email_contributor'], data['commits'], data['last_commit_date']])

print('Data written to azure_repos_contributors.csv')
