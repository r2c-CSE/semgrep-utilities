import requests

# Replace with your actual API key
SEMGREP_API_KEY = ""
BASE_URL = "https://semgrep.dev/api/v1/deployments/{deployment-slug}"


def get_projects_with_tag(tag):
    url = f"{BASE_URL}/projects"
    headers = {
        "Authorization": f"Bearer {SEMGREP_API_KEY}",
        "Content-Type": "application/json"
    }

    filtered_projects = []
    page = 0
    page_size = 100

    while True:
        params = {"page": page, "page_size": page_size}
        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            raise Exception(f"Failed to retrieve projects: {response.status_code} - {response.text}")

        data = response.json()
        projects = data.get("projects", [])

        # Filter projects by tag
        filtered_projects.extend(
            [project["name"] for project in projects if tag in project.get("tags", [])]
        )

        if len(projects) < page_size:
            break

        page += 1

    return filtered_projects


def main():
    search_tag = input("Enter the tag to search for: ")
    projects = get_projects_with_tag(search_tag)

    if projects:
        print(f"Projects containing the tag '{search_tag}':")
        for project in projects:
            print(f"{project}")
    else:
        print(f"No projects found with the tag '{search_tag}'")


if __name__ == "__main__":
    main()

