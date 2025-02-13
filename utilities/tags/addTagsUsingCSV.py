import csv
import requests

SEMGREP_API_KEY = ""
API_URL = "https://semgrep.dev/api/v1/deployments/{deployment-slug}/projects/{project_name}/tags"
# Path to your CSV file
CSV_FILE = "projects_tags.csv"

# Headers for API request
def get_headers():
    return {
        "Authorization": f"Bearer {SEMGREP_API_KEY}",
        "Content-Type": "application/json"
    }



def add_tag_to_project(project_name, tag):
    """Send API request to add tag to project"""
    url = API_URL.format(project_name=project_name)
    payload = {"tags": [tag]}
    response = requests.put(url, json=payload, headers=get_headers())
    
    if response.status_code == 200:
        print(f"Successfully added tag '{tag}' to project {project_name}")
    else:
        print(f"Failed to add tag '{tag}' to project {project_name}: {response.text}")

def main():
    with open(CSV_FILE, newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',')  # Assuming comma-delimited file
        for row in reader:
            repository = row["repository"].strip()
            tag = row["tag"].strip()
            
            project_name = repository
            if project_name:
                add_tag_to_project(project_name, tag)
            else:
                print(f"Project '{repository}' not found.")

if __name__ == "__main__":
    main()

