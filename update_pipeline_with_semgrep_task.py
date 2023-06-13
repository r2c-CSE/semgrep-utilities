# automation of adding Semgrep scan step to existing ADO classic pipelines
# find the name of the classic build pipeline per repo? 
#   Is this standard or different? 
#   do they have single pipeline per repo?
# once we have the name of the pipeline, we can get the definitionID of the pipeline
#    GET https://dev.azure.com/{organization}/{project}/_apis/build/definitions/{definitionId}?api-version=7.0
#   https://learn.microsoft.com/en-us/rest/api/azure/devops/build/definitions/get?view=azure-devops-rest-7.0
# then we update the pipeline with the new step (add agent and taskgroup)
#   PUT https://dev.azure.com/{organization}/{project}/_apis/build/definitions/{definitionId}?api-version=7.0
#   https://learn.microsoft.com/en-us/rest/api/azure/devops/build/definitions/update?view=azure-devops-rest-7.0

# Psuedo Code
# (1) get the list of all pipelines in the org
# (2) get the "build" pipeline from list of all pipelines
# (3) get the definitionID of the "build" pipeline
# (4) once we get the definitionID, we can get the "build" pipeline config
# (5) now, update the "build" pipeline config by adding a new "phase" with semgrep config ['process'][]'phases']. config for phase is in classic_config_with_semgrep.json
# (6) once we update, we reread the the "build" pipeline config to get the refName for // can we get this from response object?


# What is the plan for the call 
#  (1) lets create a manual pipeline with semgrep as a task group (lets do this in nitin's org)
#  (2) use the get_classic_pipeline_config(org, project, repo_name) function to get the pipeline config & see how the task is defined
#  (3) then create a new function to update the pipeline config with the new task group (Semgrep) update_classic_pipeline_semgrep_config(org, project, repo_name)


# The following steps are done once per workspace 
# (1) Add SEMGREP_APP_TOKEN as a workspace variable:  
# (2) Generate & Add PAT as a workspace variable: https://learn.microsoft.com/en-us/azure/devops/organizations/accounts/use-personal-access-tokens-to-authenticate?view=azure-devops&tabs=Windows 

import logging
import requests
import json
import os
import ruamel.yaml
import base64
import sys

yaml = ruamel.yaml.YAML()
yaml.preserve_quotes = True
logging.basicConfig(level=logging.DEBUG)

# Constants
# Define Org, project, SEMGREP_TASK_GROUP_ID and QUEUE_ID
org = "sebasrevuelta"
project = "Chess"
SEMGREP_TASK_GROUP_ID = "6b81d9ba-52f8-431b-9d99-08054e2c4258"
QUEUE_ID = 48

# function to get classic pipeline configuration from organization/project/repo_name
def get_classic_pipeline_config(org, project):

    headers = get_headers()

    ado_pipelines_list_url = f'https://dev.azure.com/{org}/{project}/_apis/build/definitions?api-version=7.0'
    response = requests.get(ado_pipelines_list_url, headers=headers)
    data = response.json() 

    for item in data['value']:
      pipeline_id = item['id']
      pipeline_name = item['name']
      project_item = item['project']
      definition_id = project_item['id']
      if pipeline_name == "Build": ## TODO: Change name of the pipeline
        url = f'https://dev.azure.com/{org}/{definition_id}/_apis/build/Definitions/{pipeline_id}'
        response = requests.get(url, headers=headers)
        classic_pipeline_config = response.json()
        show_task_group_info(org, project)
        update_classic_pipeline_semgrep_config(org, classic_pipeline_config, definition_id, pipeline_id)

# function to get the header for the connection
def get_headers():
    authorization = str(base64.b64encode(bytes(':'+ado_token, 'ascii')), 'ascii')

    headers = {
        'Accept': 'application/json',
        'Authorization': 'Basic '+authorization
    }
    return headers

# function to get the header for the connection
def get_headers_with_content():
    authorization = str(base64.b64encode(bytes(':'+ado_token, 'ascii')), 'ascii')

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Basic '+authorization
    }
    return headers

def show_task_group_info(org, project):

    headers = get_headers() 
    url = f'https://dev.azure.com/{org}/{project}/_apis/distributedtask/taskgroups?api-version=7.0'
    response = requests.get(url, headers=headers)
    print("***** Task Group config *****")
    pretty_data_json = json.loads(response.text)
    print (json.dumps(pretty_data_json, indent=2))
    print("***** Task Group config *****")

# function to update classic pipeline with semgrep task group
def update_classic_pipeline_semgrep_config(org, classic_pipeline_config, definition_id, pipeline_id):

    url = f'https://dev.azure.com/{org}/{definition_id}/_apis/build/Definitions/{pipeline_id}?api-version=7.0'

    headers = get_headers_with_content()

    # Add Semgrep task to the classic_pipeline_config
    semgrep_step = {
        "steps": [
          {
            "enabled": True,
            "continueOnError": True,
            "alwaysRun": True,
            "displayName": "Semgrep-Task-Group",
            "timeoutInMinutes": 0,
            "retryCountOnTaskFailure": 0,
            "condition": "succeededOrFailed()",
            "task": {
              "id": SEMGREP_TASK_GROUP_ID,
              "versionSpec": "1.*",
              "definitionType": "metaTask"
            },
            "inputs": {}
          }
        ],
        "name": "Semgrep-Task-Group",

        "target": {
          "queue": {
            "_links": {
              "self": {
                "href": "https://dev.azure.com/" + org + "/_apis/build/Queues/" + str(QUEUE_ID)
              }
            },
            "id": QUEUE_ID,
            "url": "https://dev.azure.com/" + org +  "/_apis/build/Queues/" + str(QUEUE_ID),
          },
          "agentSpecification": {
            "identifier": "ubuntu-latest"
          },
          "executionOptions": {
            "type": 0
          },
          "allowScriptsAuthAccessOption": False,
          "type": 1
        },
        "jobAuthorizationScope": "project",  # this is mandatory
    }
    classic_pipeline_config['process']['phases'].insert(0, semgrep_step)

    # Send the API request
    response = requests.put(url, headers=headers, data=json.dumps(classic_pipeline_config))

    # find refName for new phase to be used to update dependency of build pipeline
    logging.debug('This is the response from the API call to update the pipeline config')
    logging.debug(" *********** ")
    logging.debug(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
    logging.debug(" *********** ")

## START PROCESS
# Read ADO personal access token from Environment Variable
try:  
    ado_token = os.getenv("ADO_TOKEN") # Azure DevOps Personal Access Token

except KeyError: 
    logging.error("Please set the environment variable ado_token") 
    sys.exit(1)

get_classic_pipeline_config(org, project)