# The following steps are done once per workspace 
# (1) Add SEMGREP_APP_TOKEN as a workspace variable: https://support.atlassian.com/bitbucket-cloud/docs/variables-and-secrets/  
# (2) Generate & Add PAT as a workspace variable: https://support.atlassian.com/bitbucket-cloud/docs/workspace-access-tokens/ 
# more details in this video tutorial: https://www.loom.com/share/c5c4b42124834323bfc818fd02ada039 
# NOTE: you only perform the above tasks, once per workspace (not once per repo)

# we need 2 files in your local directory for where you trigger the python script:
# (1) semgrep-bitbucket-pipelines-branches.yml
# (2) semgrep-bitbucket-pipelines-pull-requests.yml

# Also, you will need the following ENV variables: BITBUCKET_TOKEN, SEMGREP_APP_TOKEN

# Steps performed by the python script below:
# clone repo from BB Cloud to your local machine 
# create a new local branch 
# replace existing file- bitbucket-pipelines.yml
# now update the bitbucket-pipelines.yml file, as follows:
# push local changes to the remote (BB cloud)
# create a PR using our API: https://developer.atlassian.com/cloud/bitbucket/rest/api-group-pullrequests/#api-repositories-workspace-repo-slug-pullrequests-post
# possibly delete these clones after the process is completed

import logging
import requests
import json
import os
from git import Repo
import time
import shutil
import pprint
import ruamel.yaml

yaml = ruamel.yaml.YAML()
yaml.preserve_quotes = True
logging.basicConfig(level=logging.DEBUG)

############################################################################################
# Read BitBucket Token from Environment Variable
############################################################################################

try:  
    bitbucket_token = os.getenv("BITBUCKET_TOKEN")
except KeyError: 
    logging.error("Please set the environment variable bitbucket-token") 
    sys.exit(1)

############################################################################################
# Define Workspace,  Repo Name and Bitbucket pipeline file
############################################################################################
workspace_name = "r2c-examples"
repo_name = "owaspwebgoatphp"
bitbucket_pipeline_file = "bitbucket-pipelines.yml"
############################################################################################
# create new directory
############################################################################################

current_epoch_time = time.time()
new_folder = f"cloned-{current_epoch_time}"
path = os.path.join(os.getcwd(), new_folder)
os.mkdir(path)
print(path)

############################################################################################
# clone repo from BB Cloud (make sure to clone from master/main)
############################################################################################

git_url = f"https://x-token-auth:{bitbucket_token}@bitbucket.org/{workspace_name}/{repo_name}.git"
to_path = f"./{new_folder}/"
repo = Repo.clone_from(git_url, to_path)

############################################################################################
# create new head and get it tracked in the origin
############################################################################################

branch_name = f"add_semgrep-{current_epoch_time}"
repo.head.reference = repo.create_head(branch_name)

############################################################################################
# define main branch (will be done using API in the future)
############################################################################################
main_branch = "master"

############################################################################################
# open the file & add semgrep CI pipeline steps- bitbucket-pipelines.yml
############################################################################################

# Get the current working directory
cwd = os.getcwd()

# Print the current working directory
print("Current working directory: {0}".format(cwd))

new_dir = cwd + '/' + new_folder

# copy the "semgrep-bitbucket-pipelines-branches.yml" file from parent to cloned dir. 
shutil.copyfile(f"{cwd}/semgrep-ci/bitbucket/semgrep-bitbucket-pipelines-branches.yml", f"{new_dir}/semgrep-bitbucket-pipelines-branches.yml")

# copy the "semgrep-bitbucket-pipelines-pull-requests.yml" file from parent to cloned dir. 
shutil.copyfile(f"{cwd}/semgrep-ci/bitbucket/semgrep-bitbucket-pipelines-pull-requests.yml", f"{new_dir}/semgrep-bitbucket-pipelines-pull-requests.yml")

os.chdir(new_dir)


with open(bitbucket_pipeline_file, "r") as fp:
    bitbucket_pipeline_data = yaml.load(fp)
logging.debug(f"********************************************* \n bitbucket-pipelines.yml \n ********************************************* {bitbucket_pipeline_data}")

with open("semgrep-bitbucket-pipelines-branches.yml", "r") as fp:
    semgrep_config = yaml.load(fp)
logging.debug(f"********************************************* \n semgrep-bitbucket-pipelines-branches.yml \n ********************************************* {semgrep_config}")

# custom logic to add semgrep-bitbucket-pipelines-branches.yml to bitbucket-pipelines.yml
if "pipelines" in bitbucket_pipeline_data:
    if "branches" in bitbucket_pipeline_data["pipelines"]:
        if main_branch in bitbucket_pipeline_data["pipelines"]["branches"]:
            for item in semgrep_config["pipelines"]["branches"][main_branch]:
                logging.debug(f"********************************************* \n printing item from pipelines --> branches --> master: \n ********************************************* {item}")
                bitbucket_pipeline_data["pipelines"]["branches"][main_branch].append(item)
        else :
            for (k,v) in semgrep_config["pipelines"]["branches"].items():
                logging.debug(f"********************************************* \n printing item from pipelines --> branches: \n ********************************************* {k} \n {v}")
                bitbucket_pipeline_data["pipelines"]["branches"][k]=v
    else :
        for (k,v) in semgrep_config["pipelines"].items():
            logging.debug(f"********************************************* \n printing item from pipelines: \n ********************************************* {k} \n {v}")
            bitbucket_pipeline_data["pipelines"][k]=v

logging.debug(f"********************************************* \n bitbucket_pipeline_data after step 1: branches \n ********************************************* {bitbucket_pipeline_data}")

with open("semgrep-bitbucket-pipelines-pull-requests.yml", "r") as fp:
    semgrep_config_pr = yaml.load(fp)
logging.debug(f"********************************************* \n semgrep-bitbucket-pipelines-pull-requests.yml \n ********************************************* {semgrep_config_pr}")

# custom logic to add semgrep-bitbucket-pipelines-pull-requests.yml to bitbucket-pipelines.yml
if "pipelines" in bitbucket_pipeline_data:
    if "pull-requests" in bitbucket_pipeline_data["pipelines"]:
        if "**" in bitbucket_pipeline_data["pipelines"]["pull-requests"]:
            for item in semgrep_config_pr["pipelines"]["pull-requests"]["**"]:
                bitbucket_pipeline_data["pipelines"]["pull-requests"]["**"].append(item)
        else: 
            for (k,v) in semgrep_config_pr["pipelines"]["pull-requests"].items():
                logging.debug(f"********************************************* \n printing item from pipelines --> pull-requests: \n ********************************************* {k} \n {v}")
                bitbucket_pipeline_data["pipelines"]["pull-requests"][k]=v
    else:
        for (k,v) in semgrep_config_pr["pipelines"].items():
            logging.debug(f"********************************************* \n printing item from pipelines: \n ********************************************* {k} \n {v}")
            bitbucket_pipeline_data["pipelines"][k]=v

logging.debug(f"********************************************* \n bitbucket_pipeline_data after step 2: pull-requests \n ********************************************* {bitbucket_pipeline_data}")

with open(bitbucket_pipeline_file, "w") as f:
    yaml.dump(bitbucket_pipeline_data, f)

############################################################################################
# stage the changed file and commit it
############################################################################################

repo.index.add(bitbucket_pipeline_file)
repo.index.commit("Added Semgrep steps to bitbucket-pipelines.yml")

############################################################################################
# push the staged commits to BitBucket
############################################################################################

push_res = repo.remotes.origin.push(branch_name)[0]
logging.debug(push_res.summary)

############################################################################################
# create a PR using BB API: https://developer.atlassian.com/cloud/bitbucket/rest/api-group-pullrequests/#api-repositories-workspace-repo-slug-pullrequests-post
############################################################################################

url = f"https://api.bitbucket.org/2.0/repositories/{workspace_name}/{repo_name}/pullrequests"

headers = {
  "Accept": "application/json",
  "Content-Type": "application/json",
  "Authorization": f"Bearer {bitbucket_token}"
}

payload = json.dumps( {
  "title": "Adding Semgrep Support",
  "source": {
    "branch": {
      "name": branch_name,
    },
    }
} )

response = requests.request(
   "POST",
   url,
   data=payload,
   headers=headers
)

logging.debug(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))

############################################################################################
# Merge PR to main using BB API: https://developer.atlassian.com/cloud/bitbucket/rest/api-group-pullrequests/#api-repositories-workspace-repo-slug-pullrequests-pull-request-id-merge-post
############################################################################################

data = json.loads(response.text)
pull_request_id = data['id']
print(pull_request_id)

url = f"https://api.bitbucket.org/2.0/repositories/{workspace_name}/{repo_name}/pullrequests/{pull_request_id}/merge"

payload = json.dumps( {
  "type": "test",
  "message": "Added Semgrep Support to bitbucket-pipelines.yml",
  "close_source_branch": True,
  "merge_strategy": "merge_commit"
} )

response = requests.request(
   "POST",
   url,
   data=payload,
   headers=headers
)

print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))