#!/usr/bin/python
import json
import os
import requests
from dotenv import load_dotenv
from google.auth import identity_pool
from google.cloud import storage, vision
import base64
from random import randint

load_dotenv()
OKTA_CLIENT_ID=os.environ.get("OKTA_CLIENT_ID")
OKTA_SECRET=os.environ.get("OKTA_SECRET")
PROJECT_ID=os.environ.get("PROJECT_ID")
OKTA_TOKEN_URL=os.environ.get("OKTA_TOKEN_URL")

def get_okta_token():
    cookies = {
        'JSESSIONID': ''.join(["{}".format(randint(0, 9)) for num in range(0, 14)])
    }

    #Client ID and Client Secret from Okta's application configuration section
    client_id = OKTA_CLIENT_ID
    client_secret = OKTA_SECRET
    # Encode data into base 64
    encodedData = base64.b64encode(bytes(f"{client_id}:{client_secret}", "ISO-8859-1")).decode("ascii")

    # Headers to make a reuest to receive access tokens
    headers = {
        'Accept': '*/*',
        'Authorization': 'Basic '+encodedData,
        'Cache-Control': 'no-cache',
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    # Grant type credentials as this is a machine to machine interactions
    data = {
        'grant_type': 'client_credentials'
    }

    # Make a request to an Okta APi endpoint
    response = requests.post(OKTA_TOKEN_URL,
                             headers=headers, cookies=cookies, data=data)
    response.raise_for_status()
    print("Creating Okta token file")
    data = response.json()
    
    # Create a file and dump the token response into a Okta-token file
    with open('okta-token.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def list_buckets(project, scoped_credentials):
    print("Calling Google Cloud Storage APIs")
    storage_client = storage.Client(project=project, credentials=scoped_credentials)
    buckets = storage_client.list_buckets()
    print('########## Showing access to Cloud Storage data #############')
    for bucket in buckets:
        print(bucket.name)

def vision_api_test(scoped_credentials):
    image_uri = 'gs://cloud-samples-data/vision/using_curl/shanghai.jpeg'

    client = vision.ImageAnnotatorClient(credentials=scoped_credentials)
    image = vision.Image()
    image.source.image_uri = image_uri

    response = client.label_detection(image=image)
    print('########## Showing access to Vision API data ##########')
    print('Labels (and confidence score):')
    print('=' * 30)
    for label in response.label_annotations:
        print(label.description, '(%.2f%%)' % (label.score*100.))

if __name__ == '__main__':
    print("Running main")
    get_okta_token()
    project=PROJECT_ID
    file = open('client-config.json')
    json_config_info = json.loads(file.read())
    scopes = ['https://www.googleapis.com/auth/cloud-vision','https://www.googleapis.com/auth/devstorage.read_only']
    credentials = identity_pool.Credentials.from_info(json_config_info)
    scoped_credentials = credentials.with_scopes(scopes)
    list_buckets(project, scoped_credentials)
    vision_api_test(scoped_credentials)
    print("Removing Okta token file")
    os.remove('okta-token.json')