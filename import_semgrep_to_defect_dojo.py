import requests
import sys
import os

URL_DEFECT_DOJO = "http://0.0.0.0:8080"   

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