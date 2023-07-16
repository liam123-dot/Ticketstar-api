"""

This function will be used to verify phone number and emails

requires client id

uses cognito ConfirmSignUp:

https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_ConfirmSignUp.html

request syntax:
{
   "ClientId": "string",
   "ConfirmationCode": "string",
   "SecretHash": "string",
   "Username": "string"
}

"""

import os
import json
import logging
import boto3
import botocore.exceptions

from utils import get_secret_hash


logger = logging.getLogger()
logger.setLevel(logging.INFO)

cognito = boto3.client('cognito-idp')

CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")


def lambda_handler(event, context):

    try:
        body = json.loads(event['body'])
        username = body['email'].lower()
        confirmation_code = body['confirmation_code']
    except (KeyError, json.JSONDecodeError) as e:
        logger.error('Error processing body. Error: %s, with event: %s', e, event)  # log the error
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': str(e),
                'reason': 'InvalidBody' if isinstance(e, KeyError) else 'InvalidBodyJson'
            })
        }
    except Exception as e:
        logger.error('Unknown error processing body. Error: %s, with event: %s', e, event)
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': str(e),
                'reason': 'Exception',
                'error': str(e)
            })
        }

    try:
        secret_hash = get_secret_hash(username=username, CLIENT_ID=CLIENT_ID, CLIENT_SECRET=CLIENT_SECRET)

        cognito.confirm_sign_up(
            ClientId=CLIENT_ID,
            SecretHash=secret_hash,
            Username=username,
            ConfirmationCode=confirmation_code
        )

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': "User confirmation successful",
            })
        }

    except botocore.exceptions.ClientError as e:
        error = e.response['Error']
        error_code = error['code']
        logger.error('Client error confirm_sign_up: %s, with event %s', error, event)  # log the error

        if error_code == 'CodeMismatchException':
            return {
                'statusCode': 401,
                'body': json.dumps({
                    'message': 'Incorrect code provided',
                    'reason': error_code,
                    'error': str(e)
                })
            }
        elif error_code == 'UserNotFoundException':
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'message': 'Invalid username provided',
                    'reason': error_code,
                    'error': str(e)
                })
            }
        else:
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'message': "Server error",
                    'reason': error_code,
                    'error': str(e)
                })
            }
    except Exception as e:
        logger.error('Client error confirm_sign_up: %s, with event %s', e, event)  # log the error

        return {
            'statusCode': 500,
            'body': {
                'message': "Internal Server Error",
                'reason': 'Exception',
                'error': str(e)
            }
        }

