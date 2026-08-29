import csv
import requests
from datetime import datetime
import sys
import time
import json

# ------------------------------------------------------------
# Configuration ⚙️⚙️⚙️
# ------------------------------------------------------------

ORGSLUG = "yourorgsluggoeshere"  # Replace with your organization slug (found in Settings > Identifiers)
BEARER_TOKEN = "yourkeygoeshere"  # Replace with your bearer token (generate one in Settings > Tokens)

# ------------------------------------------------------------
# NO EDITING BELOW THIS LINE
# ------------------------------------------------------------

API_ENDPOINT = "https://semgrep.dev/api/v1/deployments/{deployment_slug}/projects/{project_name}"

def extract_error_message(response_text):
    """Extract error message from JSON response"""
    try:
        error_json = json.loads(response_text)
        if "error" in error_json:
            return error_json["error"]
        return response_text
    except json.JSONDecodeError:
        return response_text

def delete_project(project_name):
    """
    Delete a project using the Semgrep API
    Returns a tuple of (success, message)
    """
    url = API_ENDPOINT.format(
        deployment_slug=ORGSLUG,
        project_name=project_name
    )
    
    headers = {
        "Authorization": f"Bearer {BEARER_TOKEN}"
    }
    
    try:
        response = requests.delete(url, headers=headers)
        if response.status_code == 200:
            print(f"Successfully deleted project: {project_name}")
            return True, "deleted"
        else:
            error_msg = extract_error_message(response.text)
            print(f"Failed to delete project: {project_name}")
            print(f"Error: {error_msg}")
            return False, error_msg
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        print(f"Error deleting project {project_name}: {str(e)}")
        return False, error_msg

def count_projects_in_csv():
    try:
        with open('input.csv', 'r') as file:
            return sum(1 for row in csv.reader(file) if row) - 1
    except FileNotFoundError:
        print("Error: input.csv file not found")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred while reading the CSV: {str(e)}")
        sys.exit(1)

def main():
    project_count = count_projects_in_csv()
    print(f"\nThe script will attempt to delete {project_count} projects, would you like to continue?")
    confirmation = input("Enter Y/N >>> ")
    
    if confirmation.lower() != 'y':
        print("\nOperation cancelled by user\n")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"bulkDeleteProjectsRun-{timestamp}.csv"
    results = []

    try:
        with open('input.csv', 'r') as file:
            csv_reader = csv.reader(file)
            next(csv_reader, None)
            
            for row in csv_reader:
                if row:  
                    project_name = row[0].strip()  
                    success, status = delete_project(project_name)
                    results.append([project_name, status])
                    time.sleep(0.25) 

        with open(output_filename, 'w', newline='') as output_file:
            csv_writer = csv.writer(output_file)
            csv_writer.writerow(['Project Name', 'Status'])
            csv_writer.writerows(results)
            
        print(f"\nResults have been saved to {output_filename}")
                    
    except FileNotFoundError:
        print("Error: input.csv file not found")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
