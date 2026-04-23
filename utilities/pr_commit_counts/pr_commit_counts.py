import requests
import os
from datetime import datetime, timedelta

def get_paginated_results(url, headers):
    """ Function to handle pagination for GitHub API requests """
    results = []
    while url:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            results.extend(response.json())
            if 'next' in response.links.keys():
                url = response.links['next']['url']
            else:
                url = None
        else:
            raise Exception(f"GitHub API request failed with status code {response.status_code}")
    return results

def get_repos(BASE_URL, organization, headers):
    """ Get a list of repositories for a given organization """
    url = f"{BASE_URL}/orgs/{organization}/repos"
    return get_paginated_results(url, headers)

def get_pull_requests(BASE_URL, organization, repo, headers):
    """ Get a list of pull requests for a given repository """
    url = f"{BASE_URL}/repos/{organization}/{repo}/pulls?state=all"
    return get_paginated_results(url, headers)

def get_commits_for_pull_request(BASE_URL, organization, repo, pull_number, headers):
    """ Get a list of commits for a given pull request """
    url = f"{BASE_URL}/repos/{organization}/{repo}/pulls/{pull_number}/commits"
    return get_paginated_results(url, headers)

def main():
    organization = os.getenv("GITHUB_ORG")
    if organization is None:
        organization = input("Enter the organization name: ")
    
    github_token = os.getenv('GITHUB_TOKEN') # "" # Replace with your GitHub token
    BASE_URL = "https://api.github.com"

    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json'
    }

    total_commits = 0
    total_prs = 0

    repos = get_repos(BASE_URL, organization, headers)

    for repo in repos:
        repo_name = repo['name']
        pull_requests = get_pull_requests(BASE_URL, organization, repo_name, headers)
        for pr in pull_requests:
            commits = get_commits_for_pull_request(BASE_URL, organization, repo_name, pr['number'], headers)
            one_year_ago = datetime.now() - timedelta(days=365)
            commits_in_pr_repo_last_year = sum(1 for commit in commits if datetime.strptime(commit['commit']['author']['date'], '%Y-%m-%dT%H:%M:%SZ') > one_year_ago)

            print(f'total number of commits in repo: {repo_name}, pr-#{pr["number"]}, pr-title: {pr["title"][:32]}, head: {pr["head"]["ref"][:16]} into base: {pr["base"]["ref"][:16]}  - {commits_in_pr_repo_last_year}')
            total_prs += 1
            total_commits += commits_in_pr_repo_last_year

    annual_pr_events_count, annual_pr_count = total_commits, total_prs
    avg_monthly_pr_events_count = (int(100*annual_pr_events_count/12))/100
    avg_monthly_pr_count = (int(100*annual_pr_count/12))/100
    print(f"total number of pull request events in the past 1 year: {annual_pr_events_count}")
    print(f"average number of pull request events per month in the past 1 year: {avg_monthly_pr_events_count}")
    print(f"total number of pull requests in the past 1 year: {annual_pr_count}")
    print(f"average number of pull requests per month in the past 1 year: {avg_monthly_pr_count}")


if __name__ == "__main__":
    main()
