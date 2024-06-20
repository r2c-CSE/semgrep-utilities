import os
import subprocess
import requests

BASE_URL_GITHUB = 'https://api.github.com'

def semgrep_scan(org, repo, path_bytes):
   try:
       env = os.environ.copy()
       env['SEMGREP_REPO_NAME'] = f'{org}/{repo}'
       env['SEMGREP_REPO_DISPLAY_NAME'] = f'{org}/{repo}'
       result = subprocess.run(["semgrep","ci","--code"], env=env, cwd=path_bytes, capture_output=True, text=True)
       print("Return code:", result.returncode)
       print("stdout:", result.stdout)
       print("stderr:", result.stderr)
       print(f'Successfully ran semgrep scan for {repo}')
   except subprocess.CalledProcessError as e:
       print(f"Error occurred while scanning {repo}: {e}")
   except MemoryError as e:
       print(f"Memory error occurred while scanning {repo}: {e}")
   except Exception as e:
       print(f"Unexpected error occurred while scanning {repo}: {e}")
   finally:
        # Perform any cleanup or logging if necessary
        pass


def get_github_repos_data(gh_token, org):
    repos = []
    page = 1
    while True:
        try:
            print(f'Getting github repos data for {org} page {page}')
            url = f"{BASE_URL_GITHUB}/users/{org}/repos?type=all&page={page}&per_page=100"
            headers = {'Authorization': f'token {gh_token}'}
            response = requests.get(url, headers=headers)
            page_repos = response.json()
            if not isinstance(page_repos, list):
                break
            if page_repos:
                repos.extend(page_repos)
                page += 1
            else:
                break
        except Exception as e:
            break 
    return repos

if __name__ == "__main__":
    print("Executing semgrep through all repositories")
    ORG_NAME = os.getenv("ORG_NAME")
    print(f"Organization: {ORG_NAME}")
    gh_token = os.getenv("GITHUB_TOKEN")
    repositories = get_github_repos_data(gh_token, ORG_NAME)
    for repo in repositories:
            repo_name = repo['name']
            repo_url = repo['html_url']
            repo_path = f"./{repo_name}"
            print(f"Name: {repo_name}, URL: {repo_url}")
            result = subprocess.run(["git","clone",f"{repo_url}"])
            semgrep_scan(ORG_NAME, repo_name, repo_path)
    print('********************************************')
