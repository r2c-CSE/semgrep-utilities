import requests
from requests.auth import HTTPBasicAuth

# === Configuration ===
ADO_PAT = "Your-ADO-PAT-TOKEN"
SEMGREP_APP_TOKEN = "YOUR-SEMGREP-TOKEN-WITH-API-ACCESS"
DEPLOYMENT_ID = "YOUR-SEMGREP-DEPLOYMENT-ID"
SEMGREP_API_URL = f"https://semgrep.dev/api/scm/deployments/{DEPLOYMENT_ID}/configs"

# === Common Auth Setup ===
auth = HTTPBasicAuth('', ADO_PAT)

# === Step 1: Get current user's profile (to find member ID) ===
profile_url = "https://app.vssps.visualstudio.com/_apis/profile/profiles/me?api-version=6.0"
profile_resp = requests.get(profile_url, auth=auth)
profile_resp.raise_for_status()
profile_data = profile_resp.json()
member_id = profile_data["id"]

print(f"Authenticated as: {profile_data.get('displayName')} ({profile_data.get('emailAddress')})")

# === Step 2: Get all ADO organizations for this member ===
orgs_url = f"https://app.vssps.visualstudio.com/_apis/accounts?memberId={member_id}&api-version=6.0"
orgs_resp = requests.get(orgs_url, auth=auth)
orgs_resp.raise_for_status()
orgs = orgs_resp.json().get("value", [])

if not orgs:
    print("❌ No organizations found for this PAT.")
    exit(1)

print(f"\n✅ Found {len(orgs)} organization(s).")

# === Step 3: Enumerate projects for each org ===
headers = {
    "Authorization": f"Bearer {SEMGREP_APP_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}

for org in orgs:
    org_name = org["accountName"]
    print(f"\n=== Organization: {org_name} ===")

    projects_url = f"https://dev.azure.com/{org_name}/_apis/projects?api-version=7.0"
    projects = []

    # Handle pagination if needed
    while projects_url:
        r = requests.get(projects_url, auth=auth)
        r.raise_for_status()
        data = r.json()
        projects.extend(data.get("value", []))
        projects_url = data.get("nextLink")

    print(f"  → Found {len(projects)} project(s).")

    # === Step 4: Add each project to Semgrep ===
    for project in projects:
        project_name = project["name"]
        namespace = f"{org_name}/{project_name}"

        print(f"    Creating Semgrep SCM config for: {namespace}")

        scm_payload = {
            "baseUrl": "https://dev.azure.com",
            "type": "SCM_TYPE_AZURE_DEVOPS",
            "namespace": namespace,
            "accessToken": ADO_PAT,
            "autoScan": True,
            "active": True,
        }

        resp = requests.post(SEMGREP_API_URL, headers=headers, json=scm_payload)

        if resp.status_code == 201:
            print(f"      ✅ Added {namespace} successfully.")
        elif resp.status_code == 409:
            print(f"      ⚠️  {namespace} already exists in Semgrep.")
        else:
            print(f"      ❌ Failed to add {namespace} (status {resp.status_code})")
            print("         Response:", resp.text)
