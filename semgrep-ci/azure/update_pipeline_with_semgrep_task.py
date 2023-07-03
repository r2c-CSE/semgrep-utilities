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
logging.basicConfig(level=logging.INFO)

# Constants
# Define Org, project, SEMGREP_TASK_GROUP_ID
org = "sebasrevuelta"
project = "Chess"
SEMGREP_TASK_GROUP_ID = "6b81d9ba-52f8-431b-9d99-08054e2c4258"
SEMGREP_TASK_GROUP_NAME = "Semgrep-Task-Group"
SEMGREP_VARIABLE_GROUP_NAME = "Semgrep_Variables"

def get_variables_group(org, project):
  
  headers = get_headers()
  ado_pipelines_list_url = f'https://dev.azure.com/{org}/{project}/_apis/distributedtask/variablegroups?api-version=7.0'
  response = requests.get(ado_pipelines_list_url, headers=headers)
  pretty_data_json = json.loads(response.text)
  print (json.dumps(pretty_data_json, indent=2))

def get_var_group_id(org, project):
  
  headers = get_headers()
  ado_pipelines_list_url = f'https://dev.azure.com/{org}/{project}/_apis/distributedtask/variablegroups?api-version=7.0'
  response = requests.get(ado_pipelines_list_url, headers=headers)
  data = response.json() 
  for vars_group in data['value']:
     if vars_group['name'] == SEMGREP_VARIABLE_GROUP_NAME:
        return vars_group['id']
  return 1

def get_semgrep_token(org, project):
  
  headers = get_headers()
  ado_pipelines_list_url = f'https://dev.azure.com/{org}/{project}/_apis/distributedtask/variablegroups?api-version=7.0'
  response = requests.get(ado_pipelines_list_url, headers=headers)
  data = response.json() 
  for vars_group in data['value']:
     if vars_group['name'] == SEMGREP_VARIABLE_GROUP_NAME:
        return vars_group['variables']['SEMGREP_APP_TOKEN']['value']
  return None

# function to get classic pipeline configuration from organization/project/repo_name
def add_semgrep_task_to_classic_pipeline_config(org, project):

    headers = get_headers()

    ado_pipelines_list_url = f'https://dev.azure.com/{org}/{project}/_apis/build/definitions?api-version=7.0'
    response = requests.get(ado_pipelines_list_url, headers=headers)
    data = response.json() 

    semgrep_token = get_semgrep_token(org, project)
    var_id = get_var_group_id(org, project)

    for pipeline in data['value']:
      try:
        pipeline_id = pipeline['id']
        pipeline_name = pipeline['name']
        print("Updating pipeline: " + pipeline_name)
        project_item = pipeline['project']
        definition_id = project_item['id']
        queue_id = pipeline['queue']['id']
        url = f'https://dev.azure.com/{org}/{definition_id}/_apis/build/Definitions/{pipeline_id}'
        response = requests.get(url, headers=headers)
        classic_pipeline_config = response.json()
        #show_task_group_info(org, project)
        if (check_existance_semgrep_task(classic_pipeline_config) == False):
          add_semgrep_task(org, classic_pipeline_config, definition_id, pipeline_id, queue_id)
        else:
          print("Semgrep task group: " + SEMGREP_TASK_GROUP_NAME + " already exists for pipeline: " + pipeline_name)

        ## TODO: check if variableGroups already exists but no Semgrep_Variables and get SEMGREP_APP_TOKEN AND var_id

        if (check_existance_semgrep_variable(classic_pipeline_config) == False):
          print("Addding Semgrep variable group: " + SEMGREP_VARIABLE_GROUP_NAME + " for pipeline: " + pipeline_name)
          add_semgrep_variable(org, classic_pipeline_config, definition_id, pipeline_id, semgrep_token, var_id)
        else:
          print("Semgrep variable group: " + SEMGREP_VARIABLE_GROUP_NAME + " already exists for pipeline: " + pipeline_name)   
      except:
        continue
# check if semgrep variable already exists in the pipeline
def check_existance_semgrep_task(classic_pipeline_config):
  for phase in classic_pipeline_config['process']['phases']:
    phase_name = phase['name']
    if (phase_name == SEMGREP_TASK_GROUP_NAME):
      return True
  return False

# check if semgrep task already exists in the pipeline
def check_existance_semgrep_variable(classic_pipeline_config):
  if classic_pipeline_config.get('variableGroups') is not None:
    for var_groups in classic_pipeline_config['variableGroups']:
      var_group_name = var_groups['name']
      if (var_group_name == SEMGREP_VARIABLE_GROUP_NAME):
        return True
  return False


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
        'Authorization': 'Basic '+ authorization
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
def add_semgrep_task(org, classic_pipeline_config, definition_id, pipeline_id, queue_id):

    url = f'https://dev.azure.com/{org}/{definition_id}/_apis/build/Definitions/{pipeline_id}?api-version=7.0'

    headers = get_headers_with_content()

    # Add Semgrep task to the classic_pipeline_config
    semgrep_step = {
        "steps": [
          {
            "enabled": True,
            "continueOnError": True,
            "alwaysRun": True,
            "displayName": SEMGREP_TASK_GROUP_NAME,
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
        "name": SEMGREP_TASK_GROUP_NAME,

        "target": {
          "queue": {
            "_links": {
              "self": {
                "href": "https://dev.azure.com/" + org + "/_apis/build/Queues/" + str(queue_id)
              }
            },
            "id": queue_id,
            "url": "https://dev.azure.com/" + org +  "/_apis/build/Queues/" + str(queue_id),
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

    logging.debug('This is the response from the API call to update the pipeline config')
    logging.debug(" *********** ")
    logging.debug(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
    logging.debug(" *********** ")

# function to update dependency order
def update_dependency_order(org, project):
   
    headers = get_headers()
    ado_pipelines_list_url = f'https://dev.azure.com/{org}/{project}/_apis/build/definitions?api-version=7.0'
    response = requests.get(ado_pipelines_list_url, headers=headers)
    data = response.json() 

    for item in data['value']:
      try:
        pipeline_id = item['id']
        pipeline_name = item['name']
        print("Setting semgrep dependency for pipeline: " + pipeline_name)
        project_item = item['project']
        definition_id = project_item['id']
        url = f'https://dev.azure.com/{org}/{definition_id}/_apis/build/Definitions/{pipeline_id}'
        response = requests.get(url, headers=headers)
        classic_pipeline_config = response.json()
        refName = classic_pipeline_config['process']['phases'][0]['refName']
        set_order(org, definition_id, pipeline_id, classic_pipeline_config, refName)
      except:
        continue

def set_order(org, definition_id, pipeline_id, classic_pipeline_config, refName):

    # Add dependency
    dependencies_statement = [
                    {
                        "event": "Completed",
                        "scope": refName
                    }
        ]

    classic_pipeline_config['process']['phases'][1]["dependencies"] = dependencies_statement

    # Send the API request
    headers_with_content = get_headers_with_content()
    url = f'https://dev.azure.com/{org}/{definition_id}/_apis/build/Definitions/{pipeline_id}?api-version=7.0'
    response = requests.put(url, headers=headers_with_content, data=json.dumps(classic_pipeline_config))
    logging.debug('This is the response from the API call to update dependency order')
    logging.debug(" *********** ")
    logging.debug(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
    logging.debug(" *********** ")


def add_semgrep_variable(org, classic_pipeline_config, definition_id, pipeline_id, semgrep_token, var_id):

  # Add variable group
  var_group = {
        "variables": {
          "SEMGREP_APP_TOKEN": {
            "value": semgrep_token
          }
        },
        "type": "Vsts",
        "name": SEMGREP_VARIABLE_GROUP_NAME,
        "description": SEMGREP_VARIABLE_GROUP_NAME,
        "id": var_id
      }

  var_group_as_array = [
     {
        "variables": {
          "SEMGREP_APP_TOKEN": {
            "value": semgrep_token
          }
        },
        "type": "Vsts",
        "name": SEMGREP_VARIABLE_GROUP_NAME,
        "description": SEMGREP_VARIABLE_GROUP_NAME,
        "id": var_id
      }
  ]

  # Add a new element
  if classic_pipeline_config.get('variableGroups') is None:
    classic_pipeline_config['variableGroups'] = var_group_as_array
  else:
    classic_pipeline_config['variableGroups'].append(var_group)
  
  # Send the API request
  headers_with_content = get_headers_with_content()
  url = f'https://dev.azure.com/{org}/{definition_id}/_apis/build/Definitions/{pipeline_id}?api-version=7.0'
  response = requests.put(url, headers=headers_with_content, data=json.dumps(classic_pipeline_config))
  logging.debug('This is the response from the API call to update dependency order')
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

classic_pipeline_config = add_semgrep_task_to_classic_pipeline_config(org, project)
update_dependency_order(org, project)