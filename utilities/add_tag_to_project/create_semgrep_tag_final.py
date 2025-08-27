#!/usr/bin/env python3
"""
Semgrep Repository Tag Creation Script (Working Version)

This script creates tags for Semgrep repositories using the Semgrep API.
Requires SEMGREP_APP_TOKEN environment variable to be set.
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
    tag_value: Optional[str] = None,
    api_token: Optional[str] = None
) -> bool:
    """
    Create a tag for a Semgrep repository using the repository name.
    
    Args:
        organization_slug: The organization slug (with underscores)  
        repository_name: The full repository name (e.g., 'owner/repo')
        tag_name: The name of the tag to create
        tag_value: Optional value for the tag (if None, creates simple tag)
        api_token: API token (defaults to SEMGREP_APP_TOKEN env var)
    
    Returns:
        bool: True if successful, False otherwise
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
    
    # Create new tag (simple tag or key:value format)
    if tag_value is None:
        new_tag = tag_name
        print(f"Creating simple tag: '{tag_name}'")
    else:
        new_tag = f"{tag_name}:{tag_value}"
        print(f"Creating key-value tag: '{tag_name}:{tag_value}'")
    
    # Check if tag already exists and update, or add new
    updated_tags = []
    tag_found = False
    
    for existing_tag in current_tags:
        # For simple tags, check exact match
        # For key-value tags, check if it starts with tag_name:
        if tag_value is None:
            if existing_tag == tag_name:
                tag_found = True
                print(f"Tag '{tag_name}' already exists")
                updated_tags.append(existing_tag)  # Keep as-is
            else:
                updated_tags.append(existing_tag)
        else:
            if existing_tag.startswith(f"{tag_name}:"):
                updated_tags.append(new_tag)
                tag_found = True
                print(f"Updating existing tag '{tag_name}' from '{existing_tag}' to '{new_tag}'")
            else:
                updated_tags.append(existing_tag)
    
    if not tag_found:
        updated_tags.append(new_tag)
        if tag_value is None:
            print(f"Adding new simple tag '{tag_name}'")
        else:
            print(f"Adding new key-value tag '{tag_name}:{tag_value}'")
    
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
            print(f"✅ Tag operation successful!")
            # Verify by getting updated tags
            updated_project_data = get_project_from_list(organization_slug, repository_name, api_token)
            if updated_project_data:
                print(f"Verified tags: {updated_project_data.get('tags', [])}")
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
    """
    List existing tags for a Semgrep repository.
    
    Args:
        organization_slug: The organization slug (with underscores)
        repository_name: The full repository name (e.g., 'owner/repo')  
        api_token: API token (defaults to SEMGREP_APP_TOKEN env var)
    
    Returns:
        List[str]: List of tags, or None if failed
    """
    if not api_token:
        api_token = os.getenv("SEMGREP_APP_TOKEN")
        if not api_token:
            print("Error: SEMGREP_APP_TOKEN environment variable not set")
            return None
    
    project_data = get_project_from_list(organization_slug, repository_name, api_token)
    if project_data:
        return project_data.get('tags', [])
    return None


def list_all_repositories(organization_slug: str, api_token: Optional[str] = None) -> Optional[List[dict]]:
    """List all repositories in the organization"""
    if not api_token:
        api_token = os.getenv("SEMGREP_APP_TOKEN")
        if not api_token:
            print("Error: SEMGREP_APP_TOKEN environment variable not set")
            return None
    
    url = f"https://semgrep.dev/api/v1/deployments/{organization_slug}/projects"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            return data.get('projects', [])
    except Exception as e:
        print(f"Error getting repositories: {e}")
    
    return None


def main():
    """Main function to handle command line usage."""
    if len(sys.argv) < 2:
        print("Usage: python create_semgrep_tag_final.py <org_slug> [repo_name] [tag_name] [tag_value] [--list] [--list-all]")
        print()
        print("Examples:")
        print("  # Create a simple tag")
        print("  python create_semgrep_tag_final.py semgrep_org_name your_gh_org/your_repo_name Python-3.7")
        print()
        print("  # Create a key-value tag")  
        print("  python create_semgrep_tag_final.py semgrep_org_name your_gh_org/your_repo_name language Python")
        print()
        print("  # List tags for a specific repository")  
        print("  python create_semgrep_tag_final.py semgrep_org_name your_gh_org/your_repo_name --list")
        print()
        print("  # List all repositories in the organization")
        print("  python create_semgrep_tag_final.py semgrep_org_name --list-all")
        print()
        print("Environment Variables:")
        print("  SEMGREP_APP_TOKEN - Your Semgrep API token")
        sys.exit(1)
    
    org_slug = sys.argv[1]
    
    # Handle --list-all flag
    if len(sys.argv) == 3 and sys.argv[2] == "--list-all":
        repositories = list_all_repositories(org_slug)
        if repositories:
            print(f"✅ Found {len(repositories)} repositories in {org_slug}:")
            for repo in repositories:
                tags = repo.get('tags', [])
                tags_str = f" (tags: {tags})" if tags else " (no tags)"
                print(f"  - {repo.get('name')}{tags_str}")
        else:
            print("❌ Failed to get repositories")
        return
    
    if len(sys.argv) < 3:
        print("Error: Missing repository name")
        sys.exit(1)
    
    repo_name = sys.argv[2]
    
    # Handle --list flag for specific repository
    if len(sys.argv) == 4 and sys.argv[3] == "--list":
        tags = list_repository_tags(org_slug, repo_name)
        if tags is not None:
            print(f"✅ Current tags for {repo_name}: {tags}")
        else:
            print(f"❌ Repository not found or error occurred")
        return
    
    if len(sys.argv) < 4:
        print("Error: Missing tag_name")
        print("Use --list to see current tags or --list-all to see all repositories")
        sys.exit(1)
    
    tag_name = sys.argv[3]
    tag_value = sys.argv[4] if len(sys.argv) > 4 else None
    
    success = create_repository_tag(org_slug, repo_name, tag_name, tag_value)
    
    if success:
        if tag_value:
            print(f"✅ Successfully processed tag '{tag_name}={tag_value}' for repository {repo_name}")
        else:
            print(f"✅ Successfully processed tag '{tag_name}' for repository {repo_name}")
        sys.exit(0)
    else:
        print(f"❌ Failed to create tag")
        sys.exit(1)


if __name__ == "__main__":
    main()