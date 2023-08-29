import json

import boto3
from botocore.exceptions import NoCredentialsError

s3 = boto3.client('s3')
BUCKET_NAME = 'api-2-pdfbucket-1e7y72t39nzqk'


def lambda_handler(event, context):
    query_string_parameters = event['queryStringParameters']
    pdf_name = query_string_parameters['pdf_name']

    s3_url = generate_presigned_url(BUCKET_NAME, pdf_name)

    return {
        'statusCode': '200',
        'body': json.dumps({
            'url': s3_url
        })
    }


def generate_presigned_url(bucket_name, object_name, expiration=3600):
    """
    Generate a presigned URL to share an S3 object

    :param bucket_name: string
    :param object_name: string
    :param expiration: Time in seconds for which the presigned URL is valid
    :return: Presigned URL as string. If error, returns None.
    """

    s3_client = boto3.client('s3')
    try:
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': object_name},
                                                    ExpiresIn=expiration)
    except NoCredentialsError:
        print('Credentials not available')
        return None

    return response
