#!/usr/bin/env python3
"""
Find Semgrep Repository ID

This script lists all repositories in a Semgrep organization to help find the correct repository ID.
"""

import os
import sys
import json
import requests
from typing import Optional


def list_repositories(organization_slug: str, api_token: Optional[str] = None) -> Optional[dict]:
    """
    List all repositories in a Semgrep organization.
    
    Args:
        organization_slug: The organization slug (with underscores)
        api_token: API token (defaults to SEMGREP_APP_TOKEN env var)
    
    Returns:
        dict: API response with repositories, or None if failed
    """
    if not api_token:
        api_token = os.getenv("SEMGREP_APP_TOKEN")
        if not api_token:
            print("Error: SEMGREP_APP_TOKEN environment variable not set")
            return None
    
    # Semgrep API endpoint for projects (repositories)
    url = f"https://semgrep.dev/api/v1/deployments/{organization_slug}/projects"
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    try:
        print(f"Fetching repositories for organization: {organization_slug}")
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to list repositories. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None


def find_repository_by_name(repositories_data: dict, repo_name: str) -> Optional[dict]:
    """
    Find a specific repository by name in the repositories data.
    
    Args:
        repositories_data: The API response containing repositories
        repo_name: The repository name to search for
    
    Returns:
        dict: Repository data if found, None otherwise
    """
    if not repositories_data or 'projects' not in repositories_data:
        return None
    
    for project in repositories_data['projects']:
        project_name = project.get('name', '')
        if repo_name.lower() in project_name.lower() or project_name.lower() in repo_name.lower():
            return project
    
    return None


def main():
    """Main function to handle command line usage."""
    if len(sys.argv) < 2:
        print("Usage: python find_repo_id.py <org_slug> [repo_name_to_search]")
        print()
        print("Examples:")
        print("  python find_repo_id.py semgrep_kyle_sms")
        print("  python find_repo_id.py semgrep_kyle_sms js-app")
        print()
        print("Environment Variables:")
        print("  SEMGREP_APP_TOKEN - Your Semgrep API token")
        sys.exit(1)
    
    org_slug = sys.argv[1]
    search_term = sys.argv[2] if len(sys.argv) > 2 else None
    
    # List all repositories
    repos_data = list_repositories(org_slug)
    
    if not repos_data:
        print("Failed to retrieve repositories")
        sys.exit(1)
    
    print(f"✅ Found {len(repos_data.get('projects', []))} repositories")
    print()
    
    if search_term:
        # Search for specific repository
        found_repo = find_repository_by_name(repos_data, search_term)
        if found_repo:
            print(f"🎯 Found matching repository:")
            print(f"  Name: {found_repo.get('name')}")
            print(f"  ID: {found_repo.get('id')}")
            print(f"  URL: {found_repo.get('url', 'N/A')}")
            print(f"  Status: {found_repo.get('status', 'N/A')}")
            if 'tags' in found_repo:
                print(f"  Tags: {found_repo.get('tags')}")
        else:
            print(f"❌ No repository found matching '{search_term}'")
            print("\nAll available repositories:")
            for project in repos_data.get('projects', []):
                print(f"  - {project.get('name')} (ID: {project.get('id')})")
    else:
        # List all repositories
        print("All repositories:")
        for project in repos_data.get('projects', []):
            print(f"  - {project.get('name')} (ID: {project.get('id')})")
            if project.get('url'):
                print(f"    URL: {project.get('url')}")
            print()


if __name__ == "__main__":
    main()