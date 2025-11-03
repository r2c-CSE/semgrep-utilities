import requests
from requests.auth import HTTPBasicAuth

# === Configuration ===
ADO_PAT = "YOUR-AZURE-PAT"
SEMGREP_APP_TOKEN = "YOUR-SEMGREP-TOKEN-WITH-API-ACCESS"
DEPLOYMENT_ID = "YOUR-SEMGREP-ORG-ID"
BASE_SEMGREP_URL = "https://semgrep.dev/api"
SEMGREP_CONFIGS_URL = f"{BASE_SEMGREP_URL}/scm/deployments/{DEPLOYMENT_ID}/configs"

auth = HTTPBasicAuth('', ADO_PAT)
semgrep_headers = {
    "Authorization": f"Bearer {SEMGREP_APP_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}


# === Helper Function: Subscribe new SCM config to webhook ===
def subscribe_to_webhook(config_id: str, namespace: str):
    """Subscribe a new Semgrep SCM config to SCM webhook events."""
    webhook_url = f"{BASE_SEMGREP_URL}/scm/deployments/{DEPLOYMENT_ID}/subscriptions/{config_id}"
    print(f"      → Subscribing to webhook for config {config_id}...")

    webhook_payload = {
        "deploymentId": DEPLOYMENT_ID,
        "configId": config_id,
        "subscription": {
            "scmUrl": "https://dev.azure.com",
            "events": [
                "pull_request_comment_event",
                "repository_event",
                "pull_request_event"
            ]
        }
    }

    resp = requests.put(webhook_url, headers=semgrep_headers, json=webhook_payload)
    if resp.status_code == 200:
        print(f"         ✅ Webhook subscription successful for {namespace}.")
    elif resp.status_code == 409:
        print(f"         ⚠️  Webhook already subscribed for {namespace}.")
    else:
        print(f"         ❌ Failed to subscribe webhook (status {resp.status_code})")
        print("            Response:", resp.text)


# === Step 1: Get current user's ADO profile ===
profile_url = "https://app.vssps.visualstudio.com/_apis/profile/profiles/me?api-version=7.0"
profile_resp = requests.get(profile_url, auth=auth)
profile_resp.raise_for_status()
profile_data = profile_resp.json()
member_id = profile_data["id"]
print(f"Authenticated as: {profile_data.get('displayName')} ({profile_data.get('emailAddress')})")

# === Step 2: Get all organizations ===
orgs_url = f"https://app.vssps.visualstudio.com/_apis/accounts?memberId={member_id}&api-version=6.0"
orgs_resp = requests.get(orgs_url, auth=auth)
orgs_resp.raise_for_status()
orgs = orgs_resp.json().get("value", [])

if not orgs:
    print("❌ No organizations found for this PAT.")
    exit(1)

print(f"\n✅ Found {len(orgs)} organization(s).")

# === Step 3: Enumerate and create new SCM configs ===
for org in orgs:
    org_name = org["accountName"]
    print(f"\n=== Organization: {org_name} ===")

    projects_url = f"https://dev.azure.com/{org_name}/_apis/projects?api-version=7.0"
    projects = []

    while projects_url:
        r = requests.get(projects_url, auth=auth)
        r.raise_for_status()
        data = r.json()
        projects.extend(data.get("value", []))
        projects_url = data.get("nextLink")

    print(f"  → Found {len(projects)} project(s).")

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

        # === Create SCM Config ===
        resp = requests.post(SEMGREP_CONFIGS_URL, headers=semgrep_headers, json=scm_payload)

        if resp.status_code == 201:
            data = resp.json()
            config_id = data.get("config", {}).get("id")
            print(f"      ✅ Created {namespace} (Config ID: {config_id})")

            # Subscribe newly created config to webhook
            subscribe_to_webhook(config_id, namespace)

        elif resp.status_code == 409:
            print(f"      ⚠️  {namespace} already exists in Semgrep. Skipping webhook creation.")
        else:
            print(f"      ❌ Failed to create {namespace} (status {resp.status_code})")
            print("         Response:", resp.text)
