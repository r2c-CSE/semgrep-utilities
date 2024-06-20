# Scanning all GitHub repositories with Semgrep embedded in a Kubernetes pod

Execute semgrep scans from Kubernetes is a practice followed by some users. The main advantage is scalability.

## Requirements
* A valid Semgrep token.
* A valid GitHub token.
* Kubernetes tool such as minikube.
* Docker.

## Steps:
* git clone this repo
* move to the current folder: `semgrep-utilities/utilities/kubernetes/scan_all_gh_repos`
* build docker image with: `docker build -t {DOCKER_HUB_USER}/my-semgrep-image:1.0`
* edit the file `semgrep-pod.yml` to specify the variables `SEMGREP_APP_TOKEN`, `GITHUB_TOKEN` and `ORG_NAME` (your GitHub organization name) and the name of your docker image.
* run kubernetes pod: `kubectl apply -f semgrep-pod.yml`
* you can monitorize the progress with: `kubectl logs semgrep-scan`
