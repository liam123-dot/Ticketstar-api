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
    email = body['email'].lower()
    password = body['password']
    firstName = body['firstName']
    lastName = body['lastName']
    phoneNumber = body['phoneNumber']

    # Generate secret hash
    secret_hash = get_secret_hash(email)

    # Define attributes
    attributes = [
        {'Name': 'email', 'Value': email},
        {'Name': 'given_name', 'Value': firstName},
        {'Name': 'family_name', 'Value': lastName},
        {'Name': 'phone_number', 'Value': phoneNumber}
    ]

    # Register the user in Cognito
    try:
        response = cognito.sign_up(
            ClientId=CLIENT_ID,
            SecretHash=secret_hash,
            Username=email,
            Password=password,
            UserAttributes=attributes
        )

        # Return success response
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'User registered successfully'})
        }
    except ClientError as e:
        # Return error response
        return {
            'statusCode': 400,
            'body': json.dumps({'message': e.response['Error']['Message']})
        }
