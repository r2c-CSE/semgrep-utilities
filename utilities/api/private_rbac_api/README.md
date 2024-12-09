# Example usage of Semgrep internal RBAC API 

This script fetches users and teams from a Semgrep deployment, 
identifies users who are not part of any parent team, and displays them. 
It uses the Semgrep internal API and requires an API token for authentication (web session token).

## Features

- Fetches users from a specified Semgrep deployment.
- Retrieves parent teams within the deployment.
- Identifies users who are not associated with any parent team.
- Provides detailed error handling for API requests and JSON parsing.

## Requirements

- Python 3.6+
- `requests` library (`pip install requests`)
- A valid Semgrep API token (web session token)

## How to Use

### 1. Set Up Environment Variables
Before running the script, set the Semgrep API token as an environment variable:

```bash
export semgrep_api_token=<your_api_token>
python sample.py
```

### 2. Example output
* Fetching Semgrep users from URL: https://semgrep.dev/api/agent/deployments/15142/users
* Fetched 10 Semgrep users.
* Fetching Semgrep parent teams from URL: https://semgrep.dev/api/permissions/deployments/15142/teams?parent_id=null
* Fetched 5 Semgrep parent teams.
* Users without any parent team:
* Name: John Doe, Email: john.doe@example.com
* Name: Jane Smith, Email: jane.smith@example.com

## Notes
Update the `deployment_id` variable to match your deployment ID.

