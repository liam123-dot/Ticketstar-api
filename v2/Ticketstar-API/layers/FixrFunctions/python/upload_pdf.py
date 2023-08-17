import json

import boto3
import requests
from urllib.parse import urlparse

s3 = boto3.client('s3')
BUCKET_NAME = 'api-2-pdfbucket-1e7y72t39nzqk'

def upload_pdf(pdf_url, ticket_reference):

    pdf_name = 'pdf-' + str(ticket_reference)  # Extracts file name from the URL

    response = requests.get(pdf_url, stream=True)
    s3.put_object(Bucket=BUCKET_NAME, Key=pdf_name, Body=response.content)

    return {
        'statusCode': '200',
        'body': json.dumps({
            'message': f'Uploaded {pdf_name} to {BUCKET_NAME}',
            'pdf_name': pdf_name
        })
    }
