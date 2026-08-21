import os
import sys
import requests


BASE_URL = "https://semgrep.dev/api"
TOKEN = os.environ.get("SEMGREP_APP_TOKEN")

if not TOKEN:
    sys.exit("Missing SEMGREP_APP_TOKEN environment variable")


HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}


def get_deployments():
    """Retrieve all deployments available to the token."""

    url = f"{BASE_URL}/v2/deployments"

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30,
    )
    response.raise_for_status()

    return response.json().get("deployments", [])


def get_configs(deployment_id):
    """Retrieve all SCM configs for a deployment, handling pagination."""

    url = f"{BASE_URL}/scm/deployments/{deployment_id}/configs"

    configs = []
    cursor = None

    while True:
        params = {}

        if cursor:
            params["cursor"] = cursor

        response = requests.get(
            url,
            headers=HEADERS,
            params=params,
            timeout=30,
        )
        response.raise_for_status()

        data = response.json()

        configs.extend(data.get("configs", []))

        cursor = data.get("cursor")

        if not cursor:
            break

    return configs


def enable_network_broker(deployment_id, config_id):
    """Enable Network Broker for one SCM config."""

    url = (
        f"{BASE_URL}/scm/deployments/"
        f"{deployment_id}/configs/{config_id}"
    )

    payload = {
        "useNetworkBroker": True
    }

    response = requests.patch(
        url,
        headers=HEADERS,
        json=payload,
        timeout=30,
    )
    response.raise_for_status()

    return response.json()


def main():
    deployments = get_deployments()

    if not deployments:
        sys.exit("No deployments found for this token.")

    print(f"Found {len(deployments)} deployment(s).")

    updated = 0
    skipped = 0
    failed = 0

    for deployment in deployments:
        deployment_id = deployment["id"]
        deployment_name = deployment.get("name", "Unknown")

        print()
        print(
            f"Deployment: {deployment_name} "
            f"(ID: {deployment_id})"
        )

        try:
            configs = get_configs(deployment_id)
        except requests.HTTPError as exc:
            failed += 1
            print(
                f"  Failed to retrieve configs: "
                f"{exc.response.status_code} "
                f"{exc.response.text}"
            )
            continue

        print(f"  Found {len(configs)} connection(s).")

        for config in configs:
            config_id = config["id"]
            namespace = config.get("namespace", "Unknown")

            if config.get("useNetworkBroker") is True:
                print(
                    f"  [SKIP] {namespace} "
                    f"(config {config_id}) - already enabled"
                )
                skipped += 1
                continue

            try:
                enable_network_broker(
                    deployment_id,
                    config_id,
                )

                print(
                    f"  [OK]   {namespace} "
                    f"(config {config_id}) - enabled"
                )

                updated += 1

            except requests.HTTPError as exc:
                print(
                    f"  [FAIL] {namespace} "
                    f"(config {config_id}) - "
                    f"{exc.response.status_code}: "
                    f"{exc.response.text}"
                )

                failed += 1

    print()
    print("Summary")
    print("-------")
    print(f"Updated: {updated}")
    print(f"Skipped: {skipped}")
    print(f"Failed:  {failed}")


if __name__ == "__main__":
    main()
