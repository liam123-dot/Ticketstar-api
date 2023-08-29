import json

import boto3
from botocore.exceptions import ClientError


def get_secret():

    secret_name = "CognitoCreds"
    region_name = "eu-west-2"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    # Decrypts secret using the associated KMS key.
    secret = get_secret_value_response['SecretString']
    return json.loads(secret)


def lambda_handler(event, context):

    user_pool_id = get_secret()['USER_POOL_ID']


    body = json.loads(event['body'])
    user_id = body['user_id']

    cognito = boto3.client('cognito-idp')
    response = cognito.admin_get_user(
        UserPoolId=user_pool_id,
        Username=user_id
    )
    return {
        'statusCode': 200,
        'body': json.dumps({
            'username': response['Username'],
            'user_attributes': response['UserAttributes'],
            'enabled': response['Enabled']
        })
    }
