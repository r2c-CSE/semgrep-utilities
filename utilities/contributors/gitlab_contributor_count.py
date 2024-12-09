import requests
import time
import csv
from datetime import datetime, timedelta
from collections import defaultdict
import logging

class GitLabContributorCounter:
    def __init__(self, base_url, private_token, days):
        self.base_url = base_url
        self.headers = {"PRIVATE-TOKEN": private_token}
        self.days = days
        self.since_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        # Set up logging
        logging.basicConfig(level=logging.INFO, 
                            format='%(asctime)s - %(levelname)s - %(message)s',
                            handlers=[
                                logging.FileHandler("gitlab_contributor_count.log"),
                                logging.StreamHandler()
                            ])
        self.logger = logging.getLogger(__name__)

    def get_all_groups(self):
        groups = []
        page = 1
        while True:
            response = self.make_request(f"{self.base_url}/api/v4/groups?page={page}&per_page=100")
            if not response:
                break
            groups.extend(response)
            page += 1
        self.logger.debug(f"Retrieved {len(groups)} groups")
        return groups

    def get_all_projects(self, group):
        projects = []
        page = 1
        while True:
            response = self.make_request(f"{self.base_url}/api/v4/groups/{group['id']}/projects?page={page}&per_page=100")
            if not response:
                break
            projects.extend(response)
            page += 1
        self.logger.info(f"Retrieved {len(projects)} projects for group '{group['name']}' (ID: {group['id']})")
        return projects

    def get_commits(self, project):
        commits = []
        page = 1
        while True:
            response = self.make_request(f"{self.base_url}/api/v4/projects/{project['id']}/repository/commits?since={self.since_date}&page={page}&per_page=100")
            if not response:
                break
            commits.extend(response)
            page += 1
        self.logger.info(f"Retrieved {len(commits)} commits for project '{project['name']}' (ID: {project['id']})")
        return commits

    def make_request(self, url, retries=5):
        for attempt in range(retries):
            try:
                response = requests.get(url, headers=self.headers)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                if response.status_code == 429:  # Rate limit exceeded
                    wait_time = 2 ** attempt  # Exponential backoff
                    self.logger.warning(f"Rate limit exceeded. Waiting for {wait_time} seconds.")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"Error making request: {e}")
                    return None
        self.logger.error(f"Max retries reached for URL: {url}")
        return None

    def count_contributors(self):
        all_contributors = set()
        repo_contributors = defaultdict(set)

        groups = self.get_all_groups()
        for group in groups:
            projects = self.get_all_projects(group)
            for project in projects:
                commits = self.get_commits(project)
                for commit in commits:
                    contributor = commit['author_name']
                    all_contributors.add(contributor)
                    repo_contributors[project['path_with_namespace']].add(contributor)
                
                self.logger.info(f"Repository: {project['path_with_namespace']} - Contributors: {len(repo_contributors[project['path_with_namespace']])}")
                self.logger.info(f"Contributors for {project['path_with_namespace']}: {', '.join(repo_contributors[project['path_with_namespace']])}")

        self.logger.info(f"All contributors: {', '.join(all_contributors)}")
        return all_contributors, repo_contributors

    def write_to_csv(self, all_contributors, repo_contributors):
        with open('contributor_summary.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Repository', 'Number of Contributors', 'Contributors'])
            
            for repo, contributors in repo_contributors.items():
                writer.writerow([repo, len(contributors), ', '.join(contributors)])
                self.logger.info(f"CSV Entry - Repository: {repo} - Contributors: {len(contributors)}")
            
            writer.writerow([])
            writer.writerow(['Total Unique Contributors', len(all_contributors)])
            writer.writerow(['All Contributors', ', '.join(all_contributors)])

    def run(self):
        self.logger.info(f"Starting contributor count for the last {self.days} days")
        all_contributors, repo_contributors = self.count_contributors()
        self.write_to_csv(all_contributors, repo_contributors)
        self.logger.info(f"Total unique contributors in the last {self.days} days: {len(all_contributors)}")
        self.logger.info(f"Results written to contributor_summary.csv")
    
if __name__ == "__main__":
    base_url = ""  # Replace with your GitLab instance URL
    private_token = ""  # Replace with your actual private token
    days = 90  # Number of days to look back

    counter = GitLabContributorCounter(base_url, private_token, days)
    counter.run()
