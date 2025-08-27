#!/usr/bin/env python3
"""
Test different Semgrep API endpoints to find the correct one for repository tags
"""

import os
import requests

api_token = "37827ebbe2b85150d5d6fe53d749ba631338b77ab5d3919c2cf94b88dd45607a"
org_slug = "semgrep_kyle_sms"
repo_id = "3739271"
repo_name = "kyle-semgrep/js-app"

headers = {
    "Authorization": f"Bearer {api_token}",
    "Content-Type": "application/json"
}

# Test different endpoints
endpoints_to_test = [
    f"https://semgrep.dev/api/v1/deployments/{org_slug}/projects/{repo_id}",
    f"https://semgrep.dev/api/v1/deployments/{org_slug}/repos/{repo_name}",
    f"https://semgrep.dev/api/v1/deployments/{org_slug}/repos/{repo_id}",
    f"https://semgrep.dev/api/v1/projects/{repo_id}",
    f"https://semgrep.dev/api/v1/repos/{repo_name}",
]

for endpoint in endpoints_to_test:
    print(f"\n🔍 Testing: {endpoint}")
    try:
        response = requests.get(endpoint, headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if 'tags' in data:
                print(f"   ✅ Found tags: {data['tags']}")
            print(f"   Keys available: {list(data.keys())}")
        else:
            print(f"   ❌ Response: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Error: {e}")