import requests
import sys
import json
import os

URL_DEFECT_DOJO = "http://localhost:8080"


def get_defect_dojo_users():
    headers = {"Accept": "application/json", "Authorization": "Token " + DEFECT_DOJO_API_TOKEN}

    r = requests.get(URL_DEFECT_DOJO + '/api/v2/users',headers=headers)
    if r.status_code != 200:
        sys.exit(f'Get failed: {r.text}')
    print(r.text)

def get_engagements():
    headers = {"Accept": "application/json", "Authorization": "Token " + DEFECT_DOJO_API_TOKEN}

    r = requests.get(URL_DEFECT_DOJO + '/api/v2/engagements',headers=headers)
    if r.status_code != 200:
        sys.exit(f'Get failed: {r.text}')
    print(r.text)

def get_products():
    headers = {"Accept": "application/json", "Authorization": "Token " + DEFECT_DOJO_API_TOKEN}

    r = requests.get(URL_DEFECT_DOJO + '/api/v2/products',headers=headers)
    if r.status_code != 200:
        sys.exit(f'Get failed: {r.text}')
    print(r.text)


def get_product_id(product_name):
    headers = {"Accept": "application/json", "Authorization": "Token " + DEFECT_DOJO_API_TOKEN}

    r = requests.get(URL_DEFECT_DOJO + '/api/v2/products',headers=headers)
    if r.status_code != 200:
        sys.exit(f'Get failed: {r.text}')
    data = json.loads(r.text)
    for product in data['results']:
        if product['name'] == product_name:
            return product['id']

def get_engagement_id(product_id, engagement_name):
    headers = {"Accept": "application/json", "Authorization": "Token " + DEFECT_DOJO_API_TOKEN}

    r = requests.get(URL_DEFECT_DOJO + '/api/v2/engagements',headers=headers)
    if r.status_code != 200:
        sys.exit(f'Get failed: {r.text}')
    data = json.loads(r.text)
    for engagement in data['results']:
        if engagement['name'] == engagement_name:
            if engagement['product'] == product_id:
                return engagement['id']


def uploadToDefectDojo(filename, is_new_import):
    multipart_form_data = {
        'file': (filename, open(filename, 'rb')),
        'scan_type': (None, 'Semgrep JSON Report'),
        'product_name': (None, 'chess-game'),
        'engagement_name': (None, 'semgrep'),
    }

    uri = '/api/v2/import-scan/' if is_new_import else '/api/v2/reimport-scan/'
    r = requests.post(
        URL_DEFECT_DOJO + uri,
        files=multipart_form_data,
        headers={
            'Authorization': 'Token ' + DEFECT_DOJO_API_TOKEN,
        }
    )
    if r.status_code != 200:
        sys.exit(f'Post failed: {r.text}')
    print(r.text)



if __name__ == "__main__":
    try:
        DEFECT_DOJO_API_TOKEN = os.getenv("DEFECT_DOJO_API_TOKEN")
    except KeyError: 
        print("Please set the environment variable DEFECT_DOJO_API_TOKEN") 
        sys.exit(1)
    uploadToDefectDojo("report.json", False)