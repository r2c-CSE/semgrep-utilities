import requests  # Assuming this import is missing
import sys  # Assuming this import is missing

# Likely these variables are defined elsewhere in the script
headers = {"Authorization": "Bearer xxxx"}  # Replace with actual authorization
proj_name = "semgrep/semgrep-app"  # Replace with project name
cursor = None  # Initializing cursor for pagination
page_count = 0  # Counter for tracking fetched pages
all_findings = []  # List to store all fetched vulnerabilities

while True:

  url = 'https://semgrep.dev/api/v1/deployments/1/ssc-vulns' # dont forget to replace 1 with your deployment ID
  
  #Modify the payload as needed
  payload = {
    "pageSize": 100,
    "severities": [
      "CRITICAL",
      "MEDIUM",
      "HIGH"
    ],
    "exposure": [
      "REACHABLE"
    ],
    "statuses": [
      "NEW"
    ],
    "query": proj_name
  }

  if cursor:
    payload['cursor'] = cursor

  response = requests.post(url, headers=headers, json=payload)

  if response.status_code != 200:
    print(f'Get failed with status code {response.status_code}: {response.text}')
    sys.exit(1)

  data = response.json()
  findings = data.get("vulns", [])

  all_findings.extend(findings)

  print(f'Page {page_count}: Fetched {len(findings)} findings.')

  # Update the cursor if there are more findings to fetch
  if data.get('hasMore'):
    cursor = data['cursor']
  else:
    page_count += 1
    print('No more findings to fetch.')
    # Here you can process the all_findings list, analyze vulnerabilities, etc.
    break  # Break out of the loop after fetching all pages
