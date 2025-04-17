"""
Azure DevOps Contributors Script
---------------------------------
This script fetches and prints the unique contributors across all repositories
in a specified Azure DevOps organization and project.

Requirements:
- Python 3.x
- requests library

Azure DevOps Permissions Needed: or just use Full scope PAT
- Read access to Code
- Read access to Graph
- Read access to Git
- Read access to Project and Team



Before Running:
- Export your Azure Personal Access Token to the environment variable 'AZURE_PERSONAL_ACCESS_TOKEN'
- Pass in your Azure DevOps Organization Name and Project Name
"""
import requests
import os
from datetime import datetime, timedelta
import argparse
import json
import base64

class AzureDevOpsAPI:
    def __init__(self, org_name, project_name, token):
        self.org_name = org_name
        self.project_name = project_name
        
        # Debug print
        print(f"\nInitializing connection to Azure DevOps...")
        print(f"Organization: {org_name}")
        print(f"Project: {project_name}")
        
        # Ensure token is properly formatted and encoded
        token = token.strip()  # Remove any whitespace
        if not token:
            raise ValueError("Token is empty")
            
        # Debug token length (don't print the actual token)
        print(f"Token length: {len(token)} characters")
        
        token_bytes = f":{token}".encode('ascii')
        base64_token = base64.b64encode(token_bytes).decode('ascii')
        
        self.headers = {
            'Authorization': f'Basic {base64_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        self.base_url = f"https://dev.azure.com/{org_name}"
        
        # Test connection with a simple request first
        self.test_connection()
        
    def test_connection(self):
        """Test basic connectivity to Azure DevOps."""
        print("\nTesting Azure DevOps connection...")
        
        # Try to access the organization first
        org_url = f"https://dev.azure.com/{self.org_name}/_apis/projects?api-version=7.1"
        print(f"Testing organization access: {org_url}")
        
        try:
            response = requests.get(org_url, headers=self.headers)
            print(f"Organization access status code: {response.status_code}")
            print(f"Response headers: {response.headers}")
            print(f"Response content: {response.text[:200]}...")  # Print first 200 chars
            
            if response.status_code != 200:
                print("\nAuthentication Error Details:")
                print(f"Full response: {response.text}")
                print("\nPlease verify:")
                print("1. Your PAT token is correct and not expired")
                print("2. The organization name is correct")
                print("3. Your PAT token has these permissions:")
                print("   - Code (Read)")
                print("   - Project and Team (Read)")
                print("   - Graph (Read)")
                print(f"\nTry accessing {self.base_url} in your browser to verify the organization name")
                raise ValueError(f"Organization access failed with status code: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"Connection error: {str(e)}")
            raise

    def get_repositories(self):
        """Fetch all repositories in the project."""
        repositories = []
        page = 1
        while True:
            url = f"{self.base_url}/{self.project_name}/_apis/git/repositories"
            params = {
                'api-version': '7.1',
                '$top': 100,  # Max items per page
                '$skip': (page - 1) * 100
            }
            
            print(f"\nFetching repositories page {page}...")
            
            try:
                response = requests.get(url, headers=self.headers, params=params)
                print(f"Repository request status code: {response.status_code}")
                
                if response.status_code != 200:
                    print(f"Error response content: {response.text}")
                    raise ValueError(f"Error fetching repositories. Status code: {response.status_code}")
                
                data = response.json()
                page_repos = data['value']
                repositories.extend(page_repos)
                
                # Check if we've got all repositories
                if len(page_repos) < 100:
                    break
                    
                page += 1
                
            except requests.exceptions.RequestException as e:
                print(f"Repository request error: {str(e)}")
                raise
        
        print(f"Successfully found {len(repositories)} repositories")
        return repositories

    def get_repository_commits(self, repo_id, since_date):
        """Fetch commits for a specific repository since the given date."""
        all_commits = []
        page = 1
        
        while True:
            url = f"{self.base_url}/{self.project_name}/_apis/git/repositories/{repo_id}/commits"
            params = {
                'api-version': '7.1',
                'searchCriteria.fromDate': since_date,
                '$top': 100,  # Max items per page
                '$skip': (page - 1) * 100
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                print(f"Error fetching commits for repo {repo_id}. Status code: {response.status_code}")
                return []
            
            data = response.json()
            page_commits = data['value']
            all_commits.extend(page_commits)
            
            # Check if we've got all commits
            if len(page_commits) < 100:
                break
                
            page += 1
            
            # Add progress indicator for repositories with many commits
            if page % 5 == 0:
                print(f"  Retrieved {len(all_commits)} commits so far...")
        
        return all_commits

    def get_commit_authors(self, repo_id, since_date):
        """Get unique commit authors for a repository."""
        commits = self.get_repository_commits(repo_id, since_date)
        authors = set()
        for commit in commits:
            if 'author' in commit and 'email' in commit['author']:
                authors.add(commit['author']['email'].lower())
        print(f"  Found {len(commits)} total commits from {len(authors)} unique authors")
        return authors

def report_contributors(org_name, project_name, number_of_days, output_file):
    # Initialize Azure DevOps client
    token = os.environ.get("AZURE_PERSONAL_ACCESS_TOKEN")
    if not token:
        raise ValueError("Please set your AZURE_PERSONAL_ACCESS_TOKEN as an environment variable.")
    
    print(f"Connecting to Azure DevOps organization: {org_name}")
    print(f"Project: {project_name}")
    
    try:
        azure_client = AzureDevOpsAPI(org_name, project_name, token)
        
        # Calculate date range using timezone-aware datetime
        from datetime import timezone
        since_date = (datetime.now(timezone.utc) - timedelta(days=number_of_days)).isoformat()
        
        # Get all repositories
        repositories = azure_client.get_repositories()
        print(f"\nFound {len(repositories)} repositories")
        
        # Track unique contributors across all repos
        all_contributors = set()
        repo_stats = []
        
        # Process each repository
        for repo in repositories:
            print(f"\nProcessing repository: {repo['name']}")
            authors = azure_client.get_commit_authors(repo['id'], since_date)
            all_contributors.update(authors)
            repo_stats.append({
                "name": repo['name'],
                "contributors": len(authors),
                "contributor_emails": list(authors)
            })
            print(f"Found {len(authors)} contributors in this repository")
        
        # Prepare output data
        output_data = {
            "organization": org_name,
            "project": project_name,
            "date": datetime.today().date().strftime('%Y-%m-%d'),
            "number_of_days_history": number_of_days,
            "total_contributors": len(all_contributors),
            "total_repositories": len(repositories),
            "repositories": repo_stats,
            "all_contributor_emails": list(sorted(all_contributors))
        }
        
        # Write to output file if specified
        if output_file:
            with open(output_file, 'w') as file:
                json.dump(output_data, file, indent=2)
        
        # Print summary
        print(f"\nContributor Report for {org_name}/{project_name}")
        print(f"Period: Last {number_of_days} days")
        print(f"Total repositories: {len(repositories)}")
        print(f"Total unique contributors: {len(all_contributors)}")
        print("\nRepository breakdown:")
        for repo in repo_stats:
            print(f"- {repo['name']}: {repo['contributors']} contributors")
        print("\nAll contributor emails:")
        for email in sorted(all_contributors):
            print(f"- {email}")
            
    except Exception as e:
        print(f"\nError: {str(e)}")
        print("\nTroubleshooting steps:")
        print("1. Verify your PAT token is correct and not expired")
        print("2. Verify organization name and project name are correct")
        print("3. Ensure your PAT token has these permissions:")
        print("   - Code (Read)")
        print("   - Git (Read)")
        print("4. Check if you can access the project in browser")
        raise

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Get unique contributors from Azure DevOps repositories.")
    parser.add_argument("org_name", help="The name of the Azure DevOps organization.")
    parser.add_argument("project_name", help="The name of the Azure DevOps project.")
    parser.add_argument("number_of_days", type=int, help="Number of days to look over.")
    parser.add_argument("output_filename", help="A file to log output.")
    
    args = parser.parse_args()
    report_contributors(args.org_name, args.project_name, args.number_of_days, args.output_filename) 
