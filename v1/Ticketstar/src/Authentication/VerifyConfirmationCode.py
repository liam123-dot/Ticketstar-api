import boto3
import hmac
import json
import base64
import hashlib
import os
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

cognito = boto3.client('cognito-idp')

USER_POOL_ID = os.environ.get('USER_POOL_ID')
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')


def get_secret_hash(username):
    msg = username + CLIENT_ID
    dig = hmac.new(str(CLIENT_SECRET).encode('utf-8'),
                   msg=str(msg).encode('utf-8'), digestmod=hashlib.sha256).digest()
    return base64.b64encode(dig).decode()


def lambda_handler(event, context):
    body = json.loads(event['body'])
    try:
        email = body['email']
        confirmation_code = body['confirmation_code']

    except KeyError:

        logger.info(event)

        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': "Invalid body sent"
            })
        }

    secret_hash = get_secret_hash(email)

    try:

        response = cognito.confirm_sign_up(
            ClientId=CLIENT_ID,
            SecretHash=secret_hash,
            Username=email,
            ConfirmationCode=confirmation_code
        )

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': "Successful Confirmation"
            })
        }

    except ClientError as e:
        # Return error response
        return {
            'statusCode': 400,
            'body': json.dumps({'message': e.response['Error']['Message']})
        }



