import time
import requests
from datetime import datetime, timedelta

# Constants
BASE_URL = "https://api.bitbucket.org/2.0"
WORKSPACE = "r2c-examples"  # Replace with your workspace name
ACCESS_TOKEN = ""  # Replace with your access token

def get_repositories(workspace, token):
    """ Get all repositories in a workspace """
    url = f"{BASE_URL}/repositories/{workspace}"
    headers = {'Authorization': f'Bearer {token}'}
    params = { }
    repositories = []
    while url:
        response = make_request_with_retry(url, headers, params)
        repositories.extend([repo['full_name'] for repo in response.get('values', [])])
        url = response.get('next', None)
    print(f'full list of repos is {repositories}')
    return repositories

def get_commits(repository, since_date, token):
    """ Get commits for a repository since a specific date """
    url = f"{BASE_URL}/repositories/{repository}/commits"
    headers = {'Authorization': f'Bearer {token}'}
    params = {'q': f'date > {since_date}'}
    commits = []
    while url:
        response = make_request_with_retry(url, headers, params)
        commits.extend(response.get('values', []))
        url = response.get('next', None)
    return commits

def make_request_with_retry(url, headers, params, max_retries=5, initial_delay=2):
    """ Make API request with retry on rate limit errors (status 429) """
    retries = 0
    delay = initial_delay
    
    while retries < max_retries:
        response = requests.get(url, headers=headers)
        
        # Log status code and response content for debugging
        print(f"Request URL: {url}")
        print(f"Response Status Code: {response.status_code}")
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:  # Rate limit exceeded
            # Check if 'Retry-After' header is present to determine delay
            retry_after = int(response.headers.get('Retry-After', delay))
            print(f"Rate limit exceeded. Retrying after {retry_after} seconds...")
            time.sleep(retry_after)
            retries += 1
            delay = delay * 2  # Exponential backoff
        else:
            raise Exception(f"Failed to fetch data: {response.status_code} - {response.text}")
    
    raise Exception(f"Max retries exceeded for URL: {url}")

def extract_contributors(commits):
    """ Extract unique contributors from commits """
    contributors = set()
    for commit in commits:
        commit_date = commit['date']
        if commit_date > since_date:
            author = commit['author']['user']['display_name'] if 'user' in commit['author'] else commit['author']['raw']
            contributors.add(author)
        else:
            print(f"Commit date {commit_date} is older than {since_date}. Skipping...")
    return contributors

# Main script
if __name__ == "__main__":
    # Get repositories
    repositories = get_repositories(WORKSPACE, ACCESS_TOKEN)

    # Calculate date 30 days ago
    since_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%dT%H:%M:%S%z')


    # Fetch commits and extract contributors
    all_contributors = set()
    for repo in repositories:
        print(f'working on repo- {repo}')
        commits = get_commits(repo, since_date, ACCESS_TOKEN)
        print(f'number of commits in this repo- {repo} is {len(commits)}')
        contributors = extract_contributors(commits)
        print(f"Repository '{repo}' has {len(contributors)} unique contributors.")
        all_contributors.update(contributors)

    # Print unique contributors
    print("Unique contributors in the last 30 days:")
    print(len(all_contributors))
    for contributor in all_contributors:
        print(contributor)
