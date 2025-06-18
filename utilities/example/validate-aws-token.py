import boto3
import botocore.auth
import botocore.awsrequest
import botocore.credentials
from urllib.parse import urlencode

# Fill in your credentials
credentials = botocore.credentials.Credentials(
    access_key='AKIAxxxx',
    secret_key='amryyyyyyyyy',
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

# send output from above to curl 
# curl -s -o /dev/null -w "%{http_code}" "https://sts.amazonaws.com/?Action=GetCallerIdentity&Version=2011-06-15&X-Amz-Algorithm=.......xxxxxxxx"
# it shall return 200% if token is valid
