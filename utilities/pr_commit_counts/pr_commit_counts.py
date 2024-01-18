import requests
import os

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

def get_repos(organization, headers):
    """ Get a list of repositories for a given organization """
    url = f"https://api.github.com/orgs/{organization}/repos"
    return get_paginated_results(url, headers)

def get_pull_requests(organization, repo, headers):
    """ Get a list of pull requests for a given repository """
    url = f"https://api.github.com/repos/{organization}/{repo}/pulls?state=all"
    return get_paginated_results(url, headers)

def get_commits_for_pull_request(organization, repo, pull_number, headers):
    """ Get a list of commits for a given pull request """
    url = f"https://api.github.com/repos/{organization}/{repo}/pulls/{pull_number}/commits"
    return get_paginated_results(url, headers)

def main():
    # organization = input("Enter the organization name: ")
    # github_token = input("Enter your GitHub access token: ")

    organization = "ORGANIZATION_NAME" # Replace with your organization name
    github_token = os.getenv('SEMGREP_API_WEB_TOKEN') # Add your GH token as a environment variable

    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json'
    }

    total_commits = 0
    total_prs = 0

    repos = get_repos(organization, headers)

    for repo in repos:
        pull_requests = get_pull_requests(organization, repo['name'], headers)
        for pr in pull_requests:
            commits = get_commits_for_pull_request(organization, repo['name'], pr['number'], headers)
            print(f'total number of commits in repo: {repo["name"]}, pr-#{pr["number"]}, pr-title: {pr["title"][:32]}, head: {pr["head"]["ref"][:16]} into base: {pr["base"]["ref"][:16]}  - {len(commits)}')
            total_prs += 1
            total_commits += len(commits)
    
    # print(f"Total number of commits in pull requests: {total_commits}")


    annual_pr_events_count, annual_pr_count = total_commits, total_prs
    avg_monthly_pr_events_count = (int(100*annual_pr_events_count/12))/100
    avg_monthly_pr_count = (int(100*annual_pr_count/12))/100
    print(f"total number of pull request events in the past 1 year: {annual_pr_events_count}")
    print(f"average number of pull request events per month in the past 1 year: {avg_monthly_pr_events_count}")
    print(f"total number of pull requests in the past 1 year: {annual_pr_count}")
    print(f"average number of pull requests per month in the past 1 year: {avg_monthly_pr_count}")


if __name__ == "__main__":
    main()
