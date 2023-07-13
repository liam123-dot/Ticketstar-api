import json
import boto3
import hashlib
import hmac
import os
import base64
from botocore.exceptions import ClientError
import logging


logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize Cognito client
cognito = boto3.client('cognito-idp')

# Cognito configuration
USER_POOL_ID = os.environ.get('USER_POOL_ID')
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')


def get_secret_hash(username):
    msg = username + CLIENT_ID
    dig = hmac.new(str(CLIENT_SECRET).encode('utf-8'),
                   msg=str(msg).encode('utf-8'), digestmod=hashlib.sha256).digest()
    return base64.b64encode(dig).decode()


def lambda_handler(event, context):
    # Parse user data from event body
    body = json.loads(event['body'])
    username = body['email'].lower()
    password = body['password']

    # Generate secret hash

    secret_hash = get_secret_hash(username)

    # Attempt to authenticate the user
    try:
        response = cognito.initiate_auth(
            ClientId=CLIENT_ID,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password,
                'SECRET_HASH': secret_hash
            }
        )

        # Return success response along with the authentication result

        response = cognito.get_user(
            AccessToken=response['AuthenticationResult']['AccessToken']
        )

        data = response

        response = {

            'user_id': data['Username']

        }

        mapping = {
            'email_verified': 'email_verified',
            'phone_number_verified': 'phone_number_verified',
            'phone_number': 'phone_number',
            'given_name': 'first_name',
            'family_name': 'surname',
            'email': 'email'
        }

        for attribute in data['UserAttributes']:
            name = attribute['Name']
            if name in mapping.keys():
                response[mapping[name]] = attribute['Value']

        logger.info(json.dumps(response))

        return {
            'statusCode': 200,
            'body': json.dumps({
                'attributes': response
            })
        }

    except ClientError as e:
        # Return error response
        return {
            'statusCode': 400,
            'body': json.dumps({'message': e.response['Error']['Message']})
        }
