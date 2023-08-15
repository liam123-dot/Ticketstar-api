import json

import boto3

s3 = boto3.client('s3')
BUCKET_NAME = 'api-2-pdfbucket-1e7y72t39nzqk'

def lambda_handler(event, context):

    query_string_parameters = event['queryStringParameters']
    pdf_name = query_string_parameters['pdf_name']

    s3_url = f'https://s3.amazonaws.com/{BUCKET_NAME}/{pdf_name}'

    return {
        'statusCode': '200',
        'body': json.dumps({
            'url': s3_url
        })
    }
