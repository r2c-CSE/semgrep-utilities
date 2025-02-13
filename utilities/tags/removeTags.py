import csv
import requests

# Constants
SEMGREP_API_KEY = ""
API_URL = "https://semgrep.dev/api/v1/deployments/{deployment_slug}/projects/{project_name}/tags"
HEADERS = {
    "Authorization": f"Bearer {SEMGREP_API_KEY}",
    "Content-Type": "application/json"
}

# Function to remove a tag from a project
def remove_tag_from_project(project_name, tag):
    url = API_URL.format(project_name=project_name)
    payload = {"tags": [tag]}

    response = requests.delete(url, headers=HEADERS, json=payload)

    if response.status_code == 200:
        print(f"Successfully removed tag '{tag}' from project '{project_name}'")
    else:
        print(f"Failed to remove tag '{tag}' from project '{project_name}': {response.status_code} {response.text}")

# Read CSV and remove tags
csv_file = "remove_tags.csv"
with open(csv_file, mode='r') as file:
    reader = csv.DictReader(file)
    for row in reader:
        project = row['project']
        tag = row['tag']
        remove_tag_from_project(project, tag)

print("Tag removal process completed.")
