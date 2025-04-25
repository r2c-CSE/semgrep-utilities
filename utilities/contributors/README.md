# github_recent_contributors.py
This script is meant to help estimate the number of contributors that are active within a Github organization over a period of time.

The script does not use exactly the same logic as Semgrep in determining active contributors but should be helpful in determining a rough estimate.

## Usage
You'll need to first export a [Github PAT](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens) into your environment for the script to use.

Export your PAT as the variable `GITHUB_PERSONAL_ACCESS_TOKEN`.  

Example: 
```
export GITHUB_PERSONAL_ACCESS_TOKEN=ghp_BunchOfSecretStuffGoesHere
```

The Token will need the following scopes:
- repo
- read:org
- read:user
- user:email

The script takes the following arguements:
- The name of the github organization
- The number of days to look over (we recommend 90 as a safe default)
- An output filename to store the details from the execution

After you have the PAT in your environment, run this script like this:
```
python3 github_recent_contributors.py r2c-cse 90 output.json
```

## Output
Example console output:
```
Total commit authors in the last 90 days: 33
Total members in r2c-cse: 16
Total unique contributors from r2c-cse in the last 90 days: 5
```

Example output file:
```
{
    "organization": "r2c-cse",
    "date": "2023-09-26",
    "number_of_days_history": 90,
    "org_members": [
        ...
    ],
    "commit_authors": [
        ...
    ],
    "commiting_members": [
        ...
    ]
}
```

# gitlab_contributor_count.py

## Description

This Python script counts the number of unique contributors across all repositories in all groups of a GitLab Self-Managed instance. It uses the GitLab API to fetch repository and commit data for a specified time period.

## Features

- Retrieves all groups and their projects from a GitLab instance
- Fetches commits for each project within a specified time frame
- Counts unique contributors across all repositories
- Handles API rate limiting with an exponential backoff retry mechanism
- Provides detailed logging of the process
- Generates a CSV file with a summary of contributors per repository and overall unique contributors

## Requirements

- Python 
- `requests` library

## Installation

1. Clone this repository or download the script.
2. Install the required Python package:

```
pip install requests
```

## Configuration

Before running the script, you need to set up the following:

1. GitLab instance URL
2. Private token for API authentication
3. Number of days to look back for contributions

Edit the following lines at the bottom of the script:

```python
base_url = "https://your-gitlab-instance.com"  # Replace with your GitLab instance URL
private_token = "your_private_token_here"  # Replace with your actual private token
days = 3000  # Number of days to look back
```

## Usage

Run the script using Python:

```
python gitlab_contributor_count.py
```

## Output

The script generates two types of output:
- A log file named gitlab_contributor_count.log with detailed information about the process.
- A CSV file named contributor_summary.csv containing:
    - A list of repositories with their contributor counts and names
    - The total number of unique contributors across all repositories
 

## Logging
The script provides detailed logging at different levels:
- DEBUG: Detailed information about groups, projects, and commits retrieved
- INFO: Summary information about the process and results
- WARNING: Any issues encountered during execution (e.g., rate limiting)
- ERROR: Any errors that occur during the process

Logs are written to both the console and the gitlab_contributor_count.log file.

## Troubleshooting
If you encounter any issues:
- Check the gitlab_contributor_count.log file for error messages.
- Ensure your GitLab instance URL and private token are correct.
- Verify that your GitLab account has the necessary permissions to access the groups and projects.
- If you're hitting rate limits frequently, try increasing the backoff time in the make_request method.


# Bitbucket Contributor Counter

This script counts unique contributors across all repositories in a Bitbucket workspace for a specified time period.

## Features

- Counts unique contributors across all repositories in a workspace
- Configurable time period for analysis
- Handles rate limiting with exponential backoff
- Outputs results to both console and JSON file
- Uses environment variables for secure token management
- Automatic pagination handling for both repositories and commits
- Detailed logging of API requests and responses

## Prerequisites

- Python 3.x
- `requests` library
- Bitbucket access token with appropriate permissions

## Setup

1. Install the required Python package:
```bash
pip install requests
```

2. Set up your Bitbucket access token as an environment variable:
```bash
export BITBUCKET_ACCESS_TOKEN="your_token_here"
```

## Configuration

The script has the following configurable constants at the top of the file:

- `WORKSPACE`: Your Bitbucket workspace name
- `COMMITS_FROM_DAYS`: Number of days to look back for commits (default: 1000)

## Usage

Run the script:
```bash
python bitbucket_contributor_count_retry.py
```

The script will:
1. Fetch all repositories in the specified workspace (with pagination)
2. For each repository, fetch commits within the specified time period (with pagination)
3. Extract unique contributors from the commits
4. Output the results to the console
5. Save the results to a JSON file with timestamp

## Pagination

The script automatically handles pagination for:
- Repository listing: Fetches all repositories across multiple pages
- Commit history: Fetches all commits within the specified time period across multiple pages

Debug logging will show:
- Number of repositories found per page
- Total number of repositories and pages
- Number of commits found per page for each repository
- Total number of commits and pages per repository

## Output

The script generates two types of output:

1. Console output with logging information about:
   - Repository processing progress
   - Number of commits and pages per repository
   - Number of unique contributors per repository
   - Total unique contributors across all repositories
   - API request/response details (in DEBUG mode)

2. JSON file (`contributors_YYYYMMDD_HHMMSS.json`) containing:
   - Workspace name
   - Analysis period in days
   - Total number of contributors
   - Sorted list of all contributors

## Logging

The script uses Python's logging module with the following levels:
- DEBUG (default): Detailed API request/response information, pagination details
- INFO: Repository progress, counts, and results
- WARNING: Rate limit notifications

To change the logging level, modify the `level` parameter in `logging.basicConfig()`:
```python
logging.basicConfig(
    level=logging.INFO,  # Change to INFO to see less detail
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
```

## Error Handling

The script includes error handling for:
- Missing access token
- API rate limiting (with automatic retry)
- Failed API requests
- Pagination issues

## Security

- Access token is stored in environment variables, not in the code
- API requests use secure HTTPS
- Token is passed securely in request headers 

## Contributing
Contributions to improve the script are welcome. Please feel free to submit a Pull Request.
