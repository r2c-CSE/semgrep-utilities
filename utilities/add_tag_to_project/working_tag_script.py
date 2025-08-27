#!/usr/bin/env python3
"""
Working script to create Semgrep repository tags
"""

import os
import sys
import requests
import json
import urllib.parse
from typing import Optional, List


def get_project_from_list(org_slug: str, project_name: str, api_token: str) -> Optional[dict]:
    """Get project data from the projects list endpoint"""
    url = f"https://semgrep.dev/api/v1/deployments/{org_slug}/projects"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            for project in data.get('projects', []):
                if project.get('name') == project_name:
                    return project
    except Exception as e:
        print(f"Error getting project list: {e}")
    
    return None


def create_repository_tag(
    organization_slug: str,
    repository_name: str,
    tag_name: str,
    tag_value: str,
    api_token: Optional[str] = None
) -> bool:
    """
    Create a tag for a Semgrep repository using the repository name.
    """
    if not api_token:
        api_token = os.getenv("SEMGREP_APP_TOKEN")
        if not api_token:
            print("Error: SEMGREP_APP_TOKEN environment variable not set")
            return False
    
    # First, get the current project data from the list endpoint to see actual tags
    project_data = get_project_from_list(organization_slug, repository_name, api_token)
    if not project_data:
        print(f"❌ Could not find project: {repository_name}")
        return False
    
    print(f"Found project: {project_data['name']}")
    current_tags = project_data.get('tags', [])
    print(f"Current tags: {current_tags}")
    
    # Create new tag
    new_tag = f"{tag_name}:{tag_value}"
    
    # Check if tag already exists and update, or add new
    updated_tags = []
    tag_found = False
    
    for existing_tag in current_tags:
        if existing_tag.startswith(f"{tag_name}:"):
            updated_tags.append(new_tag)
            tag_found = True
            print(f"Updating existing tag '{tag_name}'")
        else:
            updated_tags.append(existing_tag)
    
    if not tag_found:
        updated_tags.append(new_tag)
        print(f"Adding new tag '{tag_name}:{tag_value}'")
    
    # Now update using the individual project endpoint
    encoded_repo_name = urllib.parse.quote(repository_name, safe='')
    url = f"https://semgrep.dev/api/v1/deployments/{organization_slug}/projects/{encoded_repo_name}"
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    payload = {"tags": updated_tags}
    
    try:
        print(f"Updating tags to: {updated_tags}")
        response = requests.patch(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code in [200, 201]:
            print(f"✅ Tag created successfully!")
            updated_project = response.json()
            print(f"New tags: {updated_project.get('tags', [])}")
            return True
        else:
            print(f"❌ Failed to create tag. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def list_repository_tags(
    organization_slug: str,
    repository_name: str,
    api_token: Optional[str] = None
) -> Optional[List[str]]:
    """List existing tags for a Semgrep repository"""
    if not api_token:
        api_token = os.getenv("SEMGREP_APP_TOKEN")
    
    project_data = get_project_from_list(organization_slug, repository_name, api_token)
    if project_data:
        return project_data.get('tags', [])
    return None


def main():
    if len(sys.argv) < 3:
        print("Usage: python working_tag_script.py <org_slug> <repo_name> [tag_name] [tag_value] [--list]")
        print()
        print("Examples:")
        print("  python working_tag_script.py semgrep_kyle_sms kyle-semgrep/js-app environment production")
        print("  python working_tag_script.py semgrep_kyle_sms kyle-semgrep/js-app --list")
        sys.exit(1)
    
    org_slug = sys.argv[1]
    repo_name = sys.argv[2]
    
    # Set the API token
    api_token = "37827ebbe2b85150d5d6fe53d749ba631338b77ab5d3919c2cf94b88dd45607a"
    
    if len(sys.argv) == 4 and sys.argv[3] == "--list":
        tags = list_repository_tags(org_slug, repo_name, api_token)
        if tags:
            print(f"✅ Current tags for {repo_name}: {tags}")
        else:
            print(f"❌ No tags found or repository not found")
        return
    
    if len(sys.argv) < 5:
        print("Error: Missing tag_name and tag_value")
        sys.exit(1)
    
    tag_name = sys.argv[3]
    tag_value = sys.argv[4]
    
    success = create_repository_tag(org_slug, repo_name, tag_name, tag_value, api_token)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()