import logging
import os
import requests
from requests.auth import HTTPBasicAuth

logging.basicConfig(level=logging.INFO, format="%(message)s")

# === Configuration ===
ADO_PAT = os.environ["ADO_PAT"]
SEMGREP_APP_TOKEN = os.environ["SEMGREP_APP_TOKEN"]
BASE_SEMGREP_URL = "https://semgrep.dev/api"

auth = HTTPBasicAuth('', ADO_PAT)
semgrep_headers = {
    "Authorization": f"Bearer {SEMGREP_APP_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}


def get_deployment_id() -> str:
    """Fetch the Semgrep deployment ID from the API."""
    resp = requests.get(f"{BASE_SEMGREP_URL}/v1/deployments", headers=semgrep_headers)
    resp.raise_for_status()
    deployments = resp.json().get("deployments", [])
    if not deployments:
        raise RuntimeError("No Semgrep deployments found for this token.")
    return str(deployments[0]["id"])


logging.info("Fetching Semgrep deployment ID...")
DEPLOYMENT_ID = get_deployment_id()
logging.info(f"✅ Using Semgrep deployment ID: {DEPLOYMENT_ID}")

SEMGREP_CONFIGS_URL = f"{BASE_SEMGREP_URL}/scm/deployments/{DEPLOYMENT_ID}/configs"


# === Helper Function: Subscribe new SCM config to webhook ===
def subscribe_to_webhook(config_id: str, namespace: str):
    """Subscribe a new Semgrep SCM config to SCM webhook events."""
    webhook_url = f"{BASE_SEMGREP_URL}/scm/deployments/{DEPLOYMENT_ID}/subscriptions/{config_id}"
    logging.info(f"      → Subscribing to webhook for config {config_id}...")

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
        logging.info(f"         ✅ Webhook subscription successful for {namespace}.")
    elif resp.status_code == 409:
        logging.info(f"         ⚠️  Webhook already subscribed for {namespace}.")
    else:
        logging.error(f"         ❌ Failed to subscribe webhook (status {resp.status_code})")
        logging.error(f"            Response: {resp.text}")


# === Step 1: Fetch organizations from ADO API ===
def get_ado_organizations() -> list[dict]:
    """Fetch all ADO organizations accessible by the authenticated user."""
    # Get the authenticated user's profile to obtain their memberId
    profile_url = "https://app.vssps.visualstudio.com/_apis/profile/profiles/me?api-version=7.0"
    profile_resp = requests.get(profile_url, auth=auth)
    profile_resp.raise_for_status()
    member_id = profile_resp.json()["id"]

    # List all organizations (accounts) the user belongs to
    accounts_url = f"https://app.vssps.visualstudio.com/_apis/accounts?memberId={member_id}&api-version=7.0"
    accounts_resp = requests.get(accounts_url, auth=auth)
    accounts_resp.raise_for_status()
    return accounts_resp.json().get("value", [])


# === Step 2: Retrieve organizations ===
logging.info("\nFetching ADO organizations...")
orgs = get_ado_organizations()
logging.info(f"\n✅ Found {len(orgs)} organization(s) via ADO API.")

# === Step 3: Enumerate and create new SCM configs ===
for org in orgs:
    org_name = org["accountName"]
    logging.info(f"\n=== Organization: {org_name} ===")

    projects_url = f"https://dev.azure.com/{org_name}/_apis/projects?api-version=7.0"
    projects = []

    while projects_url:
        r = requests.get(projects_url, auth=auth)
        r.raise_for_status()
        data = r.json()
        projects.extend(data.get("value", []))
        projects_url = data.get("nextLink")

    logging.info(f"  → Found {len(projects)} project(s).")

    for project in projects:
        project_name = project["name"]
        namespace = f"{org_name}/{project_name}"

        logging.info(f"    Creating Semgrep SCM config for: {namespace}")

        scm_payload = {
            "baseUrl": "https://dev.azure.com",
            "type": "SCM_TYPE_AZURE_DEVOPS",
            "namespace": namespace,
            "accessToken": ADO_PAT,
            "autoScan": False,
            "active": True,
        }

        # === Create SCM Config ===
        resp = requests.post(SEMGREP_CONFIGS_URL, headers=semgrep_headers, json=scm_payload)

        if resp.status_code == 201:
            data = resp.json()
            config_id = data.get("config", {}).get("id")
            logging.info(f"      ✅ Created {namespace} (Config ID: {config_id})")

            # Subscribe newly created config to webhook
            subscribe_to_webhook(config_id, namespace)

        elif resp.status_code == 409:
            data = resp.json()
            logging.info(f"      ⚠️ {namespace} already exists in Semgrep. Updating ADO PAT...")
            url = f"{SEMGREP_CONFIGS_URL}/search"
            search_payload = {
                  "filter": {
                        "namespace": namespace,
                        "type": "SCM_TYPE_AZURE_DEVOPS"
                    }
            }
            resp = requests.post(url, headers=semgrep_headers, json=search_payload)
            data = resp.json()
            config_id = data["configs"][0]["id"]
            if resp.status_code == 200:
                logging.info(f"         ✅ Found existing config with {config_id}")
                url = f"{SEMGREP_CONFIGS_URL}/{config_id}"
                resp = requests.patch(url, headers=semgrep_headers, json=scm_payload)
                if resp.status_code == 200:
                    logging.info(f"         ✅ Updated ADO PAT for {namespace}.")
                else:
                    logging.error(f"         ❌ Failed to update ADO PAT for {namespace} (status {resp.status_code})")
                    logging.error(f"            Response: {resp.text}")
            else:
                logging.error(f"         ❌ Failed to find existing config for {namespace} (status {resp.status_code})")
                logging.error(f"            Response: {resp.text}")

        else:
            logging.error(f"      ❌ Failed to create {namespace} (status {resp.status_code})")
            logging.error(f"         Response: {resp.text}")
