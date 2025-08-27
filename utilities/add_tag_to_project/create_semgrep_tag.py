#!/usr/bin/env python3
"""
Semgrep Repository Tag Creation Script

This script creates tags for Semgrep repositories using the Semgrep API.
Requires SEMGREP_APP_TOKEN environment variable to be set.
"""

import os
import sys
import json
import requests
from typing import Optional


def create_repository_tag(
    organization_slug: str,
    repository_id: str,
    tag_name: str,
    tag_value: str,
    api_token: Optional[str] = None
) -> bool:
    """
    Create a tag for a Semgrep repository.
    
    Args:
        organization_slug: The organization slug (with underscores)
        repository_id: The repository ID
        tag_name: The name of the tag to create
        tag_value: The value for the tag
        api_token: API token (defaults to SEMGREP_APP_TOKEN env var)
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not api_token:
        api_token = os.getenv("SEMGREP_APP_TOKEN")
        if not api_token:
            print("Error: SEMGREP_APP_TOKEN environment variable not set")
            return False
    
    # First get existing project to preserve current tags
    # Try using repository name format (owner/repo) instead of ID
    url = f"https://semgrep.dev/api/v1/deployments/{organization_slug}/repos/{repository_id}"
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    try:
        # Get current project data
        get_response = requests.get(url, headers=headers, timeout=30)
        if get_response.status_code != 200:
            print(f"❌ Failed to get project data. Status code: {get_response.status_code}")
            print(f"Response: {get_response.text}")
            return False
        
        project_data = get_response.json()
        existing_tags = project_data.get('tags', [])
        
        # Create new tag in the format expected by API
        new_tag = f"{tag_name}:{tag_value}"
        
        # Check if tag already exists (update scenario)
        updated_tags = []
        tag_updated = False
        
        for existing_tag in existing_tags:
            if existing_tag.startswith(f"{tag_name}:"):
                updated_tags.append(new_tag)
                tag_updated = True
                print(f"Updating existing tag '{tag_name}'")
            else:
                updated_tags.append(existing_tag)
        
        # If tag doesn't exist, add it
        if not tag_updated:
            updated_tags.append(new_tag)
            print(f"Adding new tag '{tag_name}={tag_value}'")
        
        # PATCH the project with updated tags
        payload = {
            "tags": updated_tags
        }
        
        print(f"Updating repository {repository_id} tags: {updated_tags}")
        
        response = requests.patch(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200 or response.status_code == 201:
            print(f"✅ Tag created successfully!")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"❌ Failed to create tag. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def list_repository_tags(
    organization_slug: str,
    repository_id: str,
    api_token: Optional[str] = None
) -> Optional[dict]:
    """
    List existing tags for a Semgrep repository.
    
    Args:
        organization_slug: The organization slug (with underscores)
        repository_id: The repository ID
        api_token: API token (defaults to SEMGREP_APP_TOKEN env var)
    
    Returns:
        dict: API response with tags, or None if failed
    """
    if not api_token:
        api_token = os.getenv("SEMGREP_APP_TOKEN")
        if not api_token:
            print("Error: SEMGREP_APP_TOKEN environment variable not set")
            return None
    
    url = f"https://semgrep.dev/api/v1/deployments/{organization_slug}/projects/{repository_id}/tags"
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to list tags. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None


def main():
    """Main function to handle command line usage."""
    if len(sys.argv) < 5:
        print("Usage: python create_semgrep_tag.py <org_slug> <repo_id> <tag_name> <tag_value> [--list]")
        print()
        print("Examples:")
        print("  python create_semgrep_tag.py my_org 12345 environment production")
        print("  python create_semgrep_tag.py my_org 12345 team security")
        print("  python create_semgrep_tag.py my_org 12345 --list (to list existing tags)")
        print()
        print("Environment Variables:")
        print("  SEMGREP_APP_TOKEN - Your Semgrep API token")
        sys.exit(1)
    
    org_slug = sys.argv[1]
    repo_id = sys.argv[2]
    
    # Check if --list flag is provided
    if len(sys.argv) == 4 and sys.argv[3] == "--list":
        print(f"Listing tags for repository {repo_id} in organization {org_slug}...")
        tags = list_repository_tags(org_slug, repo_id)
        if tags:
            print(f"✅ Tags retrieved successfully:")
            print(json.dumps(tags, indent=2))
        return
    
    if len(sys.argv) < 5:
        print("Error: Missing tag_name and tag_value arguments")
        sys.exit(1)
    
    tag_name = sys.argv[3]
    tag_value = sys.argv[4]
    
    success = create_repository_tag(org_slug, repo_id, tag_name, tag_value)
    
    if success:
        print(f"✅ Successfully created tag '{tag_name}={tag_value}' for repository {repo_id}")
        sys.exit(0)
    else:
        print(f"❌ Failed to create tag")
        sys.exit(1)


if __name__ == "__main__":
    main()