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

def get_contributors(org_name, number_of_days):
    token = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")
    if not token:
        raise ValueError("Please set your GITHUB_PERSONAL_ACCESS_TOKEN as an environment variable.")
    headers = {'Authorization': f'token {token}'}
    
    # Fetch all repositories in the organization
    response = requests.get(
        f'https://api.github.com/orgs/{org_name}/repos',
        headers=headers
    )
    repos = response.json()

    # Date range calculation
    since_date = (datetime.utcnow() - timedelta(days=number_of_days)).isoformat() + "Z"
    until_date = datetime.utcnow().isoformat() + "Z"

    unique_contributors = set()

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
        else:
            print(f"Repo: {repo_name} is empty.") 
        
    # Print unique contributors and their total count        
    print(f"Unique contributors in the last {number_of_days} days:", unique_contributors)
    print(f"Total number of unique contributors in the last {number_of_days} days:", len(unique_contributors))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Get unique contributors from a GitHub organization.")
    parser.add_argument("org_name", help="The name of the GitHub organization.")
    parser.add_argument("number_of_days", type=int, help="Number of days to look over.")
    
    args = parser.parse_args()
    get_contributors(args.org_name, args.number_of_days)
