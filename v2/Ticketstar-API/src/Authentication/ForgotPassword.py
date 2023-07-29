"""

Function called when a user has forgotten their password. Uses:

https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_ForgotPassword.html

"""

import os
import json
import boto3
import botocore.exceptions
import re

from utils import get_secret_hash
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

cognito = boto3.client('cognito-idp')

USER_POOL_ID = os.environ.get('USER_POOL_ID')
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')


def lambda_handler(event, body):

    input_type = ''
    try:
        body = json.loads(event['body'])
        user_input = body['user_input'].lower()

        email_regex = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
        phone_regex = re.compile(r'^\+44\d{10}$')

        if email_regex.match(user_input):
            input_type = 'email'
        elif phone_regex.match(user_input):
            input_type = 'phone_number'
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'message': 'Invalid input'
                })
            }

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

    username = check_user_exists(user_input, input_type)

    if username is None:
        return {
            'statusCode': '400',
            'body': json.dumps({
                'message': 'User with provided inputs does not exits',
                'reason': 'UserNotFoundException'
            })
        }
    
    secret_hash = get_secret_hash(username, CLIENT_ID, CLIENT_SECRET)

    try:

        forgot_password_response = cognito.forgot_password(
            ClientId=CLIENT_ID,
            SecretHash=secret_hash,
            Username=username
        )

        delivery_details = forgot_password_response['CodeDeliveryDetails']

        return {
            'statusCode': 200,
            'body': json.dumps({
                'DeliveryMedium': delivery_details['DeliveryMedium'],
                'Destination': delivery_details['Destination'],
                'user_id': username
            })
        }

    except botocore.exceptions.ClientError as e:
        error = e.response['Error']
        error_code = error['Code']
        logger.error('Client error: %s, with event %s', error, event)  # log the error

        if error_code in ['UserNotFoundException', 'ResourceNotFoundException']:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'message': 'Invalid username',
                    'reason': 'UserNotFoundException'
                })
            }
        else:
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'message': 'Internal Error',
                })
            }
    except Exception as e:
        logger.error("Unknown exception: %s", str(e))
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Internal error'
            })
        }


def check_user_exists(user_input, input_type):
    response = cognito.list_users(
        UserPoolId=USER_POOL_ID,
        AttributesToGet=[
            input_type
        ],
        Filter=f"{input_type}='{user_input}'"
    )

    if len(response['Users']) > 0:
        return response['Users'][0]['Username']

    return None
