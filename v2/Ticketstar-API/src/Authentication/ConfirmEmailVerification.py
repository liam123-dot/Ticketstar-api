"""

Called after the InitiateEmailVerification. Codes will be valid for 1 hour.

"""
import time

from DatabaseConnector import Database
import json
import logging
import boto3
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

cognito = boto3.client('cognito-idp')

USER_POOL_ID = os.environ.get('USER_POOL_ID')
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')

def get_user_id(email):
    response = cognito.list_users(
        UserPoolId=USER_POOL_ID,
        Filter=f"email='{email}'"
    )

    if len(response['Users']) == 0:
        return None

    try:
        username = response['Users'][0]['Username']
    except KeyError:
        return None

    return username


def set_email_verified(username):
    response = cognito.admin_update_user_attributes(
        UserPoolId=USER_POOL_ID,
        Username=username,
        UserAttributes=[
            {
                'Name': 'email_verified',
                'Value': 'true'
            }
        ]
    )
    logger.info(response)


def lambda_handler(event, context):

    try:
        body = json.loads(event['body'])
        email = body['user_email']
        code = body['code']
    except KeyError as e:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Invalid key sent: ' + str(e)
            })
        }
    except Exception as e:
        logger.error("Error: %s", str(e))
        return {
            'statusCode': 500
        }

    try:

        with Database() as database:
            sql = "SELECT email_verification_code, timeout FROM VerificationCodes WHERE user_email=%s"

            results = database.execute_select_query(sql, (email, ))

    except Exception as e:
        logger.info("Database exception: %s", e)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'internal error'
            })
        }

    if len(results) == 0:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Email verification has not been initiated'
            })
        }

    result = results[0]

    email_verification_code = result[0]
    timeout = result[1]

    current_time = time.time()

    if timeout < current_time:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Code timeout',
                'Reason': 'CodeTimeout'
            })
        }

    if str(email_verification_code) != str(code):
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Incorrect code',
                'reason': 'IncorrectCode'
            })
        }

    username = get_user_id(email)
    set_email_verified(username)

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Email successfully verified'
        })
    }

