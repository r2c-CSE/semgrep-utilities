import time
import requests
import json
import logging
import os
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Constants
BASE_URL = "https://api.bitbucket.org/2.0"
WORKSPACE = "r2c-examples"  # Replace with your workspace name
COMMITS_FROM_DAYS = 1000

# Get access token from environment variable
ACCESS_TOKEN = os.getenv('BITBUCKET_ACCESS_TOKEN')
if not ACCESS_TOKEN:
    logging.error("BITBUCKET_ACCESS_TOKEN environment variable is not set")
    exit(1)

def get_repositories(workspace, token):
    """ Get all repositories in a workspace """
    url = f"{BASE_URL}/repositories/{workspace}"
    headers = {'Authorization': f'Bearer {token}'}
    params = { }
    repositories = []
    page = 1
    
    while url:
        logging.debug(f"Fetching repositories page {page}")
        response = make_request_with_retry(url, headers, params)
        current_repos = [repo['full_name'] for repo in response.get('values', [])]
        repositories.extend(current_repos)
        logging.debug(f"Found {len(current_repos)} repositories on page {page}")
        url = response.get('next', None)
        page += 1
    
    logging.info(f'Found total of {len(repositories)} repositories across {page-1} pages')
    return repositories

def get_commits(repository, since_date, token):
    """ Get commits for a repository since a specific date """
    url = f"{BASE_URL}/repositories/{repository}/commits"
    headers = {'Authorization': f'Bearer {token}'}
    params = {'q': f'date > {since_date}'}
    commits = []
    page_count = 0
    
    while url:
        page_count += 1
        response = make_request_with_retry(url, headers, params)
        current_commits = response.get('values', [])
        
        # Check if any commit is older than since_date
        for commit in current_commits:
            commit_date = commit['date']
            if commit_date <= since_date:
                # If we find a commit older than since_date, we can stop
                return commits, page_count
            commits.append(commit)
            
        url = response.get('next', None)
    return commits, page_count

def make_request_with_retry(url, headers, params, max_retries=5, initial_delay=2):
    """ Make API request with retry on rate limit errors (status 429) """
    retries = 0
    delay = initial_delay
    
    while retries < max_retries:
        response = requests.get(url, headers=headers)
        
        # Log status code and response content for debugging
        logging.debug(f"Request URL: {url}")
        logging.debug(f"Response Status Code: {response.status_code}")
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:  # Rate limit exceeded
            # Check if 'Retry-After' header is present to determine delay
            retry_after = int(response.headers.get('Retry-After', delay))
            logging.warning(f"Rate limit exceeded. Retrying after {retry_after} seconds...")
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
            logging.debug(f"Commit date {commit_date} is older than {since_date}. Skipping...")
    return contributors

# Main script
if __name__ == "__main__":
    # Get repositories
    repositories = get_repositories(WORKSPACE, ACCESS_TOKEN)

    # Calculate date COMMITS_FROM_DAYS days ago
    since_date = (datetime.now() - timedelta(days=COMMITS_FROM_DAYS)).strftime('%Y-%m-%dT%H:%M:%S%z')

    # Fetch commits and extract contributors
    all_contributors = set()
    for repo in repositories:
        logging.info(f'working on repo- {repo}')
        commits, page_count = get_commits(repo, since_date, ACCESS_TOKEN)
        logging.info(f'number of commits in this repo- {repo} is {len(commits)}')
        logging.info(f'number of pages in the commits in this repo- {repo} is {page_count}')
        contributors = extract_contributors(commits)
        logging.info(f"Repository '{repo}' has {len(contributors)} unique contributors.")
        all_contributors.update(contributors)

    # Print unique contributors
    logging.info(f"Unique contributors in the last {COMMITS_FROM_DAYS} days:")
    logging.info(f"Total contributors: {len(all_contributors)}")
    for contributor in all_contributors:
        logging.info(contributor)

    # Write contributors to JSON file
    output_file = f"contributors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump({
            'workspace': WORKSPACE,
            'period_days': COMMITS_FROM_DAYS,
            'total_contributors': len(all_contributors),
            'contributors': sorted(list(all_contributors))
        }, f, indent=2)
    
    logging.info(f"\nContributors list has been written to {output_file}")
