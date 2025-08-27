#!/usr/bin/env python3
"""
Get detailed project information to understand the API structure
"""

import os
import requests
import json

api_token = "37827ebbe2b85150d5d6fe53d749ba631338b77ab5d3919c2cf94b88dd45607a"
org_slug = "semgrep_kyle_sms"

headers = {
    "Authorization": f"Bearer {api_token}",
    "Content-Type": "application/json"
}

# Get all projects and look at the structure
url = f"https://semgrep.dev/api/v1/deployments/{org_slug}/projects"

try:
    response = requests.get(url, headers=headers, timeout=30)
    if response.status_code == 200:
        data = response.json()
        
        # Find the js-app project and show all its details
        for project in data.get('projects', []):
            if 'js-app' in project.get('name', ''):
                print(f"📋 Detailed info for js-app project:")
                print(json.dumps(project, indent=2))
                print(f"\n🔑 Available keys: {list(project.keys())}")
                break
    else:
        print(f"Failed: {response.status_code} - {response.text}")
        
except Exception as e:
    print(f"Error: {e}")