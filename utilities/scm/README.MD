# Enable Semgrep Network Broker for All SCM Connections

This Python script enables the Semgrep **Network Broker** option (`useNetworkBroker: true`) for every SCM connection in the Semgrep deployment associated with the provided API token.

The script automatically discovers the deployment ID, retrieves all SCM connections, skips connections where Network Broker is already enabled, and updates the remaining connections.

## Requirements

- Python 3.8+
- `requests` Python package
- A valid Semgrep API token with permission to read and update SCM configurations

Install the required Python package:

```bash
pip install requests
```

## Authentication

The script expects the Semgrep API token in the `SEMGREP_APP_TOKEN` environment variable.

```bash
export SEMGREP_APP_TOKEN="<your-semgrep-token>"
```

You do **not** need to provide the Semgrep deployment ID. The script automatically retrieves it using:

```http
GET https://semgrep.dev/api/v2/deployments
```

## Usage

Run the script:

```bash
python3 enable_network_broker.py
```

## What the Script Does

The script performs the following steps:

1. Reads the API token from `SEMGREP_APP_TOKEN`.
2. Retrieves the Semgrep deployment information.
3. Retrieves all SCM connections for each deployment.
4. Handles pagination when retrieving SCM connections.
5. Checks whether `useNetworkBroker` is already enabled.
6. Skips connections where Network Broker is already enabled.
7. Enables Network Broker on connections where it is disabled.
8. Prints a summary of updated, skipped, and failed connections.

## APIs Used

### Retrieve Deployment

```http
GET /api/v2/deployments
```

Example response:

```json
{
  "deployments": [
    {
      "id": 1605,
      "name": "My Company Name"
    }
  ]
}
```

The returned deployment ID is then used for the SCM API requests.

### Retrieve SCM Connections

```http
GET /api/scm/deployments/{deploymentId}/configs
```

Example response:

```json
{
  "configs": [
    {
      "id": "12345",
      "namespace": "my-github-org",
      "autoScan": true,
      "useNetworkBroker": false,
      "autoScanSettings": {
        "diffEnabled": true
      },
      "hasAccessToken": true
    }
  ],
  "cursor": ""
}
```

The script follows the returned `cursor` when necessary to retrieve all connections.

### Enable Network Broker

For every connection where:

```json
{
  "useNetworkBroker": false
}
```

the script calls:

```http
PATCH /api/scm/deployments/{deploymentId}/configs/{configId}
```

with:

```json
{
  "useNetworkBroker": true
}
```

Only the `useNetworkBroker` property is modified.

The script does not intentionally modify other SCM connection settings such as:

- `autoScan`
- `namespace`
- `subscribe`
- `autoScanSettings`
- SCM credentials or access tokens

## Example

Given the following connections:

| Connection | Network Broker |
| --- | --- |
| `github-org-1` | Disabled |
| `github-org-2` | Enabled |
| `gitlab-org` | Disabled |
| `bitbucket-org` | Disabled |

Running:

```bash
python3 enable_network_broker.py
```

could produce:

```text
Found 1 deployment(s).

Deployment: My Company Name (ID: 1605)
  Found 4 connection(s).
  [OK]   github-org-1 (config 123) - enabled
  [SKIP] github-org-2 (config 456) - already enabled
  [OK]   gitlab-org (config 789) - enabled
  [OK]   bitbucket-org (config 101) - enabled

Summary
-------
Updated: 3
Skipped: 1
Failed:  0
```

## Error Handling

If an individual connection cannot be updated, the script reports the failure and continues processing the remaining connections.

For example:

```text
[FAIL] github-org (config 123) - 403: Forbidden
```

At the end of the execution, the script reports:

```text
Summary
-------
Updated: 3
Skipped: 2
Failed:  1
```

## Security

Do not hardcode the Semgrep API token in the Python script.

Use the environment variable:

```bash
export SEMGREP_APP_TOKEN="<your-semgrep-token>"
```

Avoid committing tokens to Git repositories, shell scripts, `.env` files, or CI configuration files that may be publicly accessible.

If using the script from CI/CD, store the token using the secret-management mechanism provided by the CI/CD platform.

## Notes

The operation is idempotent: connections where Network Broker is already enabled are skipped.

Running the script multiple times therefore does not repeatedly modify connections that already have:

```json
{
  "useNetworkBroker": true
}
```

## Disclaimer

Test the script against an appropriate environment before using it broadly. The script modifies SCM connection configuration through the Semgrep API.
