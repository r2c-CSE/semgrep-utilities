"""
GitHub Recent Contributors Script
---------------------------------
This script fetches and prints the unique contributors from the last 30 days
across all the repositories in a specified GitHub organization.

Directions:
1. Save this script as `github_recent_contributors.py` in a directory of your choice.
2. Open a terminal and navigate to the directory where this script is saved.
3. Install the required Python library: `pip3 install requests`
4. Run the script with: `python3 github_recent_contributors.py`

Requirements:
- Python 3.x
- A GitHub Personal Access Token

GitHub Permissions Needed:
- repo (or public_repo for public repositories)
- read:org
- read:user
- user:email 

Before Running:
- Replace 'YOUR_PERSONAL_ACCESS_TOKEN' in this script with your actual GitHub Personal Access Token.
- Replace 'YOUR_ORG_NAME' with your target GitHub organization name.
- Ensure your token has the necessary scopes and permissions.

Note:
- Keep your tokens secure and never expose them in client-side code or public repositories.
"""

import requests
from datetime import datetime, timedelta
import json
import re

def extract_pagination_links(link_header):
    links = {}
    if not link_header:
        return links

    link_pattern = r'<(?P<url>[^>]+)>;\s*rel="(?P<rel>[^"]+)"'
    
    for match in re.finditer(link_pattern, link_header):
        url = match.group('url')
        rel = match.group('rel')
        links[rel] = url

    return links

def fetch_all_commits(repo_owner, repo_name, since_date, until_date, headers):
    all_commits = []
    url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/commits'
    
    while url:
        response = requests.get(
            url,
            params={'since': since_date, 'until': until_date},
            headers=headers
        )

        commits = response.json()
        if not isinstance(commits, list):  # error handling
            break

        all_commits.extend(commits)

        # Extract pagination links and update the next URL to fetch
        link_header = response.headers.get('Link', '')
        links = extract_pagination_links(link_header)
        url = links.get('next')

    return all_commits


# Replace with your personal access token
token = "YOUR_PERSONAL_ACCESS_TOKEN"
headers = {'Authorization': f'token {token}'}

# Replace with your target organization name
org_name = "YOUR_ORG_NAME"

def fetch_org_members(org_name, headers):
    members = set()
    url = f'https://api.github.com/orgs/{org_name}/members'
    
    while url:
        response = requests.get(url, headers=headers)
        for member in response.json():
            members.add(member['login'])

        # Pagination support for members
        link_header = response.headers.get('Link', '')
        links = extract_pagination_links(link_header)
        url = links.get('next')
    
    return members

# After setting headers and before looping through repositories
org_members = fetch_org_members(org_name, headers)

# Fetch all repositories in the organization
response = requests.get(
    f'https://api.github.com/orgs/{org_name}/repos',
    headers=headers
)
repos = response.json()

# Date range for the last 30 days
since_date = (datetime.utcnow() - timedelta(days=30)).isoformat() + "Z"
until_date = datetime.utcnow().isoformat() + "Z"

unique_contributors = set()

# Loop through each repository in the organization
for repo in repos:
    owner = repo['owner']['login']
    repo_name = repo['name']
    
    commits = fetch_all_commits(owner, repo_name, since_date, until_date, headers)
    
    # Extract and collect unique contributors from commit data
    for commit in commits:
        if 'author' in commit and commit['author'] is not None:
            contributor_username = commit['author']['login']
            if contributor_username in org_members:
                unique_contributors.add(contributor_username)

        
print("Unique contributors in the last 30 days:", unique_contributors)
print("Total number of unique contributors in the last 30 days:", len(unique_contributors))
