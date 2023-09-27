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
- user:email (optional, but recommended)

Before Running:
- Export your Github Personal Access Token to the environment variable 'GITHUB_PERSONAL_ACCESS_TOKEN'
- Pass in your Github Org Name and the Number of Days over which you'd like to list contributors
- Ensure your token has the necessary scopes and permissions.

Note:
- Keep your tokens secure and never expose them in client-side code or public repositories.
"""
import requests
import os
from datetime import datetime, timedelta
import argparse
import json


def get_repos(org_name, headers):
    """Fetch all repositories for the given organization."""
    response = requests.get(
        f'https://api.github.com/orgs/{org_name}/repos',
        headers=headers
    )
    
    if response.status_code != 200:
        raise ValueError(f"Error fetching repositories for organization {org_name}. Status code: {response.status_code}")

    return response.json()

def get_organization_members(org_name, headers):
    """Fetch all members of the organization."""
    members = []
    page = 1
    while True:
        response = requests.get(
            f'https://api.github.com/orgs/{org_name}/members?page={page}',
            headers=headers
        )
        if response.status_code != 200:
            break
        members_page = response.json()
        if not members_page:
            break
        members.extend(members_page)
        page += 1
    return {member['login'] for member in members}

def get_contributors(org_name, number_of_days, headers):
    # init contributor set
    unique_contributors = set()
    unique_authors = set()
    
    # Fetch all repositories in the organization
    repos = get_repos(org_name, headers)

    # Date range calculation
    since_date = (datetime.utcnow() - timedelta(days=number_of_days)).isoformat() + "Z"
    until_date = datetime.utcnow().isoformat() + "Z"

    # Loop through each repository in the organization
    for repo in repos:
        owner = repo['owner']['login']
        repo_name = repo['name']
        
        # Fetch commits for each repository in the given date range
        response = requests.get(
            f'https://api.github.com/repos/{owner}/{repo_name}/commits',
            params={'since': since_date, 'until': until_date},
            headers=headers
        )
        
        commits = response.json()

        if isinstance(commits, list):
            for commit in commits:
                unique_contributors.add(commit['commit']['author']['name'])
                if commit['author']:
                    unique_authors.add(commit['author']['login'])
        else:
            print(f"Repo: {repo_name} is empty.") 
        
    return unique_contributors, unique_authors

def report_contributors(org_name, number_of_days, output_file):
    # init github auth
    token = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")
    if not token:
        raise ValueError("Please set your GITHUB_PERSONAL_ACCESS_TOKEN as an environment variable.")
    headers = {'Authorization': f'token {token}'}

    org_members = get_organization_members(org_name, headers)
    unique_contributors, unique_authors = get_contributors(org_name, number_of_days, headers)
    
    if output_file:
        output_data = {
            "organization": org_name,
            "date": datetime.today().date().strftime('%Y-%m-%d'),
            "number_of_days_history": number_of_days,
            "org_members": list(org_members),
            "commit_authors": list(unique_authors),
            "commiting_members": list(unique_authors & org_members)
        }

        with open(output_file, 'w') as file:
            json.dump(output_data, file)

    # Print unique contributors and their total count        
    print(f"Total commit authors in the last {number_of_days} days:", len(unique_authors))
    print(f"Total members in {org_name}:", len(org_members))
    print(f"Total unique contributors from {org_name} in the last {number_of_days} days:", len(unique_authors & org_members))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Get unique contributors from a GitHub organization.")
    parser.add_argument("org_name", help="The name of the GitHub organization.")
    parser.add_argument("number_of_days", type=int, help="Number of days to look over.")
    parser.add_argument("output_filename", help="A file to log output.")
    
    args = parser.parse_args()
    report_contributors(args.org_name, args.number_of_days, args.output_filename)


