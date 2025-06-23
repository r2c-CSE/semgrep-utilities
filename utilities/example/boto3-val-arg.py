import boto3
import botocore.auth
import botocore.awsrequest
import botocore.credentials
from urllib.parse import urlencode
import argparse
import subprocess

parser = argparse.ArgumentParser(description='Generate SigV4 signed URL for STS GetCallerIdentity')
parser.add_argument('--access-key', required=True, help='AWS Access Key ID')
parser.add_argument('--secret-key', required=True, help='AWS Secret Access Key')

args = parser.parse_args()

# Create credentials object
credentials = botocore.credentials.Credentials(
    access_key=args.access_key,
    secret_key=args.secret_key,
)

# Create the request
request = botocore.awsrequest.AWSRequest(
    method='GET',
    url='https://sts.amazonaws.com/?Action=GetCallerIdentity&Version=2011-06-15'
)

# Sign the request
signer = botocore.auth.SigV4QueryAuth(
    credentials,
    'sts',
    'us-east-1',
    expires=60
)
signer.add_auth(request)

# Output pre-signed URL
print(request.url)

# Run curl command
result = subprocess.run(
    ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", request.url],
    capture_output=True,
    text=True
)

# Extract and print HTTP status code
http_code = result.stdout.strip()
print(f"HTTP status code: {http_code}")
