#!/usr/bin/env python3
"""
Test updating project tags using the correct API endpoint
"""

import os
import requests
import json

api_token = "37827ebbe2b85150d5d6fe53d749ba631338b77ab5d3919c2cf94b88dd45607a"
org_slug = "semgrep_kyle_sms"
repo_name = "kyle-semgrep/js-app"

headers = {
    "Authorization": f"Bearer {api_token}",
    "Content-Type": "application/json"
}

# Try using the project name in the URL (URL encoded)
import urllib.parse
encoded_repo_name = urllib.parse.quote(repo_name, safe='')

endpoints_to_test = [
    f"https://semgrep.dev/api/v1/deployments/{org_slug}/projects/{encoded_repo_name}",
    f"https://semgrep.dev/api/v1/deployments/{org_slug}/projects/{repo_name}",
]

for endpoint in endpoints_to_test:
    print(f"\n🔍 Testing GET: {endpoint}")
    try:
        response = requests.get(endpoint, headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success! Current tags: {data.get('tags', [])}")
            
            # Now try to update tags
            current_tags = data.get('tags', [])
            new_tags = current_tags + ['environment:production']
            
            payload = {"tags": new_tags}
            print(f"   🔄 Trying to update with tags: {new_tags}")
            
            patch_response = requests.patch(endpoint, headers=headers, json=payload, timeout=10)
            print(f"   PATCH Status: {patch_response.status_code}")
            if patch_response.status_code in [200, 201]:
                print(f"   ✅ Tag update successful!")
                print(f"   Response: {patch_response.json()}")
            else:
                print(f"   ❌ Tag update failed: {patch_response.text}")
            break
        else:
            print(f"   ❌ Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")