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

## Contributing
Contributions to improve the script are welcome. Please feel free to submit a Pull Request.
