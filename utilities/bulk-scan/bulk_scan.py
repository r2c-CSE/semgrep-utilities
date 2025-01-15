from __future__ import annotations

import argparse
import asyncio
import json
import pathlib

import aiohttp

REQ_TEMPLATE = {
    "runs": [],
    "type": "autoscan"
}

async def send_request(index, session, url, body, semgrep_app_token):
    HEADERS = {
        "Authorization": f"Bearer {semgrep_app_token}",
        "Content-Type": "application/json",
    }

    async with session.post(url, data=json.dumps(body), headers=HEADERS) as resp:
        try:
            print(f"Making request for {url}")
            resp_body = await resp.json()
            await asyncio.sleep(0.5)
            return {
                "index": index,
                "body": resp_body, 
                "message": f"{index} {resp.status} {url}"
            }
        except Exception as e:
            print(f"Error: {e} for {url}")


async def main(repos_json_filename: str, semgrep_app_url: str, semgrep_app_token_filename: str):
    with pathlib.Path.open(repos_json_filename) as f:
        repos = json.load(f)
    
    with pathlib.Path.open(semgrep_app_token_filename) as f:
        app_token_data = json.load(f)
        secret = app_token_data['secret']

    async with aiohttp.ClientSession() as session:
        for index, repo in enumerate(repos):
            req_body = REQ_TEMPLATE.copy()  # Create a fresh request body for each repository
            req_body['runs'] = [{
                "repo_id": repo['repository_id']  # Add the repository-specific ID
            }]
            
            req_url = f"{semgrep_app_url}/api/agent/deployments/{repo['deployment_id']}/scans/run"
            print(f"Sending request for {repo['repository_id']} to {req_url}")
            
            # Send the request for this specific repository and wait for its completion
            response = await send_request(index, session, req_url, req_body, secret)
            
            # Output the response for this repository
            print(f"message: {response['message']}")
            if response['body']:
                print(f"body: {json.dumps(response['body'], indent=2)}")
            else:
                print("No body returned for this request.")

            # Optional: you could also introduce a delay if necessary between requests
            await asyncio.sleep(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repos_json_filename",
        type=str,
        required=True,
        help="Path to a JSON file containing a list of repository objects with keys `id` and `deployment_id`.",
    )
    parser.add_argument(
        "--semgrep_app_url", 
        type=str, 
        default="https://semgrep.dev"
    )
    parser.add_argument(
        "--semgrep_app_token", 
        type=str, 
        required=True,
        help="Path to a json file containing a key 'secret' and a value of the semgrep app token"
    )
    args = parser.parse_args()

    asyncio.run(
        main(args.repos_json_filename, args.semgrep_app_url, args.semgrep_app_token)
    )
