
"""

Called during the sign up process. Will send a email verification code to a provided email

"""
import json
import time

import boto3
from DatabaseConnector import Database

import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ses = boto3.client('ses')

def generate_verification_code():
    import random as r
    verification_code = r.randint(100_000, 999_999)
    return str(verification_code)


def lambda_handler(event, context):

    try:
        body = json.loads(event['body'])
        user_email = body['user_email']

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

    verification_code = generate_verification_code()

    timeout = round(time.time()) + 3600

    with Database() as database:
        sql = """
        INSERT INTO VerificationCodes(user_email, email_verification_code, timeout) VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE email_verification_code = VALUES(email_verification_code), timeout = VALUES(timeout)
        """

        database.execute_insert_query(sql, (user_email, verification_code, timeout))

    response = ses.send_email(
        Source='verify@ticketstar.uk',
        Destination={
            'ToAddresses': [
                user_email
            ]
        },
        Message={
            'Subject': {
                'Data': 'Ticketstar Verification Code'
            },
            'Body': {
                'Text': {
                    'Data': 'Your verification code is: ' + str(verification_code)
                }
            }
        },
    )

    return {
        'statusCode': 200
    }