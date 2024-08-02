import requests
import sys
import json
import os

## CUSTOMER could change these values
CREATE_WORK_ITEMS = True
FILTER_PROJECT_BY_TAG = False
TAG_TO_FILTER = "sebas"
BUILD_REQUESTEDFOREMAIL = "sebastianrevuelta@gmail.com" 
BRANCH_NAME = "master"
AREA_NAME = "WebGoat\\\Review" 
TAGS_TO_WORK_ITEMS = "semgrep"
SYSTEM_COLLECTIONURI = "https://sebasrevuelta.visualstudio.com" 
SYSTEM_TEAMPROJECT = "WebGoat" 

URL_TO_WORK_ITEMS = f"{SYSTEM_COLLECTIONURI}/{SYSTEM_TEAMPROJECT}/_apis/wit/workitems/%24task"
URL_LINK_TO_REPO = f"{SYSTEM_COLLECTIONURI}/{SYSTEM_TEAMPROJECT}/_git"


def get_deployments():
    headers = {"Accept": "application/json", "Authorization": "Bearer " + SEMGREP_APP_TOKEN}

    r = requests.get('https://semgrep.dev/api/v1/deployments',headers=headers)
    if r.status_code != 200:
        sys.exit(f'Get failed: {r.text}')
    data = json.loads(r.text)
    slug_name = data['deployments'][0].get('slug')
    print("Accessing org: " + slug_name)
    return slug_name

def get_projects(slug_name):
    
    headers = {"Accept": "application/json", "Authorization": "Bearer " + SEMGREP_APP_TOKEN}

    r = requests.get('https://semgrep.dev/api/v1/deployments/' + slug_name + '/projects?page_size=2000',headers=headers)
    if r.status_code != 200:
        sys.exit(f'Get failed: {r.text}')
    data = json.loads(r.text)
    for project in data['projects']:
        project_name = project['name']
        project_tags = project['tags']
        if FILTER_PROJECT_BY_TAG == True:
            if TAG_TO_FILTER in project_tags:
                print("Getting findings for: " + project_name)
                get_findings_per_repo(slug_name, project_name)
        else:
            print("Getting findings for: " + project_name)
            get_findings_per_repo(slug_name, project_name)


def get_findings_per_repo(slug_name, repo):
      
    headers = {"Accept": "application/json", "Authorization": "Bearer " + SEMGREP_APP_TOKEN}

    r = requests.get('https://semgrep.dev/api/v1/deployments/' + slug_name + '/findings?repos='+repo+'&page_size=3000&issue_type=sca&exposures=reachable,always_reachable',headers=headers)
    if r.status_code != 200:
        sys.exit(f'Get failed: {r.text}')
    data = json.loads(r.text)
    # Iterating through the findings
    for finding in data['findings']:
        id = str(finding['id'])
        severity = finding['severity']
        #if (severity == "high" or severity=="critical"):
        if (severity=="critical"):        
                if CREATE_WORK_ITEMS:
                    print("Creating work item for finding: " + id)
                    create_work_items(slug_name, repo, finding)
                else:
                    print("It will create a work item for finding: " + id  + ", if the flag CREATE_WORK_ITEMS is set to True.")

def create_work_items(org_name, repo_name, finding):
    
    work_item_summary = finding['rule_name']
    work_item_message = finding['rule_message']
    work_item_severity = finding['severity']
    work_item_file_info = finding['location']['file_path'] + ":" + str(finding['location']['line'])
    work_item_branch_name = finding['ref']
    work_item_branch_name = work_item_branch_name.replace("refs/heads/", "")
    work_item_vuln_code_url = f"{URL_LINK_TO_REPO}/{repo_name}" \
                              f"?path=/{finding['location']['file_path']}&" \
                              f"version=GB{work_item_branch_name}&" \
                              f"line={finding['location']['line']}&" \
                              f"lineEnd={finding['location']['end_line']}&" \
                              f"lineStartColumn={finding['location']['column']}&" \
                              f"lineEndColumn={finding['location']['end_column']}&" \
                              f"lineStyle=plain&_a=contents"
    url_to_semgrep = f"https://semgrep.dev/orgs/{org_name}/findings?repo={repo_name}&ref={work_item_branch_name}"

    html_description = "<!DOCTYPE html> <html> <body> <p> <strong>Summary: </strong>" + work_item_message + "</p> <p></p> <p><strong>Link to code: </strong><a href=" + work_item_vuln_code_url + ">" + work_item_file_info + "</a></p><p></p><p><strong>Link to project findings in Semgrep: </strong><a href=" + url_to_semgrep + ">" + url_to_semgrep + "</a></p><p></p> <p><strong>Severity: </strong>" + work_item_severity + "</p></body></html> "
    data = '[ { "op": "add", "path": "/fields/System.Title", "from": null, "value": "' + work_item_summary + '" }, { "op": "add", "path": "/fields/System.AssignedTo", "value": "'+ BUILD_REQUESTEDFOREMAIL + '" }, { "op": "add", "path": "/fields/System.Tags", "value":  "'+ TAGS_TO_WORK_ITEMS + '" },{ "op": "add", "path": "/fields/System.AreaPath", "value":  "'+ AREA_NAME + '" }, { "op": "add", "path": "/fields/System.Description", "value": "' + html_description + '" }]'
    print(data)
    params = {
        'api-version': '7.0',
    }

    headers_work_items = {
        "Content-Type": "application/json-patch+json"
    }

    r = requests.post(url=URL_TO_WORK_ITEMS,
            headers=headers_work_items, 
            params=params,
            data=data, 
            auth=('', SYSTEM_ACCESSTOKEN),
        )

    if r.status_code == 200:
        print(f"Added workitem successfully, status_code : {r.status_code}")
        return True
                  
    else:
        print(f"Error in adding workitem, status_code : {r.status_code}")
        print(f"Error in adding workitem, headers : {r.headers}")
        print(f"Error in adding workitem, text : {r.text}")
        return False



if __name__ == "__main__":
    try:  
        SEMGREP_APP_TOKEN = os.getenv("SEMGREP_APP_TOKEN") # Azure DevOps Personal Access Token
        SYSTEM_ACCESSTOKEN = os.getenv('SYSTEM_ACCESSTOKEN')
    except KeyError: 
        print("Please set the environment variables SEMGREP_APP_TOKEN and SYSTEM_ACCESSTOKEN (Azure)") 
        sys.exit(1)
    org_name = get_deployments()
    get_projects(org_name)
