import requests
import os
import sys

deployment_id = "YOUR_DEPLOYMENT_ID"

def fetch_semgrep_users(semgrep_api_token, deployment_id):
    url = f'https://semgrep.dev/api/agent/deployments/{deployment_id}/users'
    headers = {'Authorization': f'Bearer {semgrep_api_token}'}

    print(f"Fetching Semgrep users from URL: {url}")

    try:
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f"Failed to fetch Semgrep users. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return []

        response_json = response.json()
        users = response_json.get('users', [])

        print(f"Fetched {len(users)} Semgrep users.")

        return users

    except requests.RequestException as e:
        print(f"Failed to complete operation: {e}")
        return []
    except ValueError as e:
        print(f"Failed to parse JSON response: {e}")
        return []

def fetch_semgrep_parent_teams(semgrep_api_token, deployment_id):
    url = f'https://semgrep.dev/api/permissions/deployments/{deployment_id}/teams?parent_id=null'
    headers = {'Authorization': f'Bearer {semgrep_api_token}'}

    print(f"Fetching Semgrep parent teams from URL: {url}")

    try:
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f"Failed to fetch Semgrep parent teams. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return []

        response_json = response.json()
        teams = response_json.get('teams', [])

        print(f"Fetched {len(teams)} Semgrep parent teams.")

        return teams

    except requests.RequestException as e:
        print(f"Failed to complete operation: {e}")
        return []
    except ValueError as e:
        print(f"Failed to parse JSON response: {e}")
        return []

def find_users_without_parent_team(users, teams):
    # Get a set of all user IDs from the teams JSON
    user_ids_in_teams = set(
        user["userId"]
        for team in teams
        for user in team.get("users", [])
    )

    # Identify users who are not in any team
    users_without_team = [
        user for user in users if user["id"] not in user_ids_in_teams
    ]

    return users_without_team

if __name__ == "__main__":
    try:  
        semgrep_api_token = os.getenv("semgrep_api_token") 
    except KeyError: 
        print("Please set the environment variable semgrep_api_token") 
        sys.exit(1)
    users = fetch_semgrep_users(semgrep_api_token, deployment_id)
    teams = fetch_semgrep_parent_teams(semgrep_api_token, deployment_id)
    users_without_team = find_users_without_parent_team(users, teams)
    print("Users without any parent team:")
    for user in users_without_team:
        print(f"Name: {user['name']}, Email: {user['email']}")
