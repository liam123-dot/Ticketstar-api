"""

Ths file will contain the logic for when a user signs up for the platform.

This contains many aspect of error handling and verification.

We need many functions to fulfill this.
"""

"""
SignUpFunction:
Comes from the sign up screen.
Takes the following information in the body:

first_name, last_name, email, phone_number, password

uses the cognito sdk to sign up.



Response from cognito:

{
   "CodeDeliveryDetails": { 
      "AttributeName": "string",
      "DeliveryMedium": "string",
      "Destination": "string"
   },
   "UserConfirmed": boolean,
   "UserSub": "string"
}

"""

from LambdaInvokationExceptions import InvalidBodyException
from botocore.exceptions import ClientError
from utils import get_secret_hash, SecretHashGenerationException
import boto3
import json
import os
import logging


logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize Cognito client
cognito = boto3.client('cognito-idp')

# Cognito configuration
USER_POOL_ID = os.environ.get('USER_POOL_ID')
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')


def lambda_handler(event, context):
    logger.info('Processing event: %s', event)  # log the incoming event
    try:
        # Load the attributes and check whether all the required inputs are sent
        body = json.loads(event['body'])
        email = body['email'].lower()
        password = body['password']
        first_name = body['firstName']
        last_name = body['lastName']
        phone_number = body['phoneNumber']
    except (InvalidBodyException, json.JSONDecodeError) as e:
        logger.error('Error processing event: %s', e)  # log the error
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': str(e),
                'reason': 'InvalidBody' if isinstance(e, InvalidBodyException) else 'InvalidJson'
            })
        }

    try:
        confirmation_method = submit_to_cognito(email, password, first_name, last_name, phone_number)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'User successfully registered',
                'confirmation_method': confirmation_method
            })
        }
    except SecretHashGenerationException:
        logger.error('Error generating secret hash')  # log the error
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Error generating secret hash',
                'reason': 'secret_hash'
            })
        }
    except ClientError as e:
        error = e.response['Error']
        logger.error('Client error: %s', error)  # log the error
        if error['Code'] in ['UsernameExistsException', 'InvalidPasswordException']:
            return {
                'statusCode': 401,
                'body': json.dumps({
                    'message': error['Message'],
                    'reason': error['Code']
                })
            }
        elif error['Code'] == 'CodeDeliveryFailureException':
            return {
                'statusCode': 401,
                'body': json.dumps({
                    'message': error['Message'],
                    'reason': 'CodeDeliveryFailure'
                })
            }
        elif error['Code'] in ['InvalidEmailRoleAccessPolicyException', 'InvalidSmsRoleAccessPolicyException']:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'message': error['Message'],
                    'reason': error['Code']
                })
            }
        else:
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'message': 'Unexpected error occurred',
                    'reason': 'unknown_error'
                })
            }


def submit_to_cognito(email, password, first_name, last_name, phone_number):

    secret_hash = get_secret_hash(username=email, CLIENT_ID=CLIENT_ID, CLIENT_SECRET=CLIENT_SECRET)

    attributes = [
        {'Name': 'email', 'Value': email},
        {'Name': 'given_name', 'Value': first_name},
        {'Name': 'family_name', 'Value': last_name},
        {'Name': 'phone_number', 'Value': phone_number}
    ]

    response = cognito.sign_up(
        ClientId=CLIENT_ID,
        SecretHash=secret_hash,
        Username=email,
        Password=password,
        UserAttributes=attributes
    )

    confirmation_method = response['CodeDeliveryDetails']['AttributeName']

    return confirmation_method





