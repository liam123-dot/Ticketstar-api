"""

Called after the forgot password lambda is called,
takes the confirmation code, new password, and user id of the user and should notify
of any errors such as incorrect confirmation code, invalid password.

https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_ConfirmForgotPassword.html

"""
import os
import json
import boto3
import botocore.exceptions

from utils import get_secret_hash
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

cognito = boto3.client('cognito-idp')

USER_POOL_ID = os.environ.get('USER_POOL_ID')
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')


def lambda_handler(event, context):

    try:
        body = json.loads(event['body'])
        confirmation_code = body['confirmation_code']
        new_password = body['new_password']
        user_id = body['user_id']

    except KeyError as e:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Invalid body, invalid parameter: ' + str(e),
                'reason': 'Parameter'
            })
        }
    except json.JSONDecodeError as e:
        logger.error("JSON decode error: %s", str(e))
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Invalid body',
                'reason': 'Syntax'
            })
        }

    secret_hash = get_secret_hash(user_id, CLIENT_ID, CLIENT_SECRET)

    try:

        response = cognito.confirm_forgot_password(
            ClientId=CLIENT_ID,
            SecretHash=secret_hash,
            Username=user_id,
            ConfirmationCode=confirmation_code,
            Password=new_password
        )

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'password successfully changed'
            })
        }

    except botocore.exceptions.ClientError as e:
        error = e.response['Error']
        error_code = error['Code']
        logger.error('Client error: %s, with event %s', error, event)  # log the error

        if error_code == 'CodeMismatchException':
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'message': "Wrong confirmation code",
                    'reason': 'IncorrectConfirmationCode'
                })
            }
