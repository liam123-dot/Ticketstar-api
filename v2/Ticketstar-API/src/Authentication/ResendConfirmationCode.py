"""

Called when a user wants to resend a confirmation code.

"""
import json

from utils import get_secret_hash
import logging
import boto3
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

cognito = boto3.client('cognito-idp')

from GetCognitoCreds import get_secret
cognito_creds = get_secret()

USER_POOL_ID = cognito_creds['USER_POOL_ID']
CLIENT_ID = cognito_creds['CLIENT_ID']
CLIENT_SECRET = cognito_creds['CLIENT_SECRET']

def lambda_handler(event, context):

    try:

        body = json.loads(event['body'])
        email = body['email']

    except KeyError as e:

        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Invalid parameter: ' + str(e)
            })
        }

    try:

        secret_hash = get_secret_hash(email, CLIENT_ID, CLIENT_SECRET)

        response = cognito.resend_confirmation_code(
            ClientId=CLIENT_ID,
            SecretHash=secret_hash,
            Username=email
        )

        details = response['CodeDeliveryDetails']
        delivery_medium = details['DeliveryMedium']
        destination = details['Destination']

        return {
            'statusCode': 200,
            'body': json.dumps({
                'DeliveryMedium': delivery_medium,
                'Destination': destination
            })
        }

    except Exception as e:
        logger.error("Error resending verification code: %s", str(e))

        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Internal error'
            })
        }
