"""

Ths file will contain the logic for when a user signs up for the platform.

This contains many aspect of error handling and verification.

We need many functions to fulfill this.
"""
from utils import get_secret_hash

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
from botocore.exceptions import ClientError
import boto3
import json
import logging
from DatabaseConnector import Database

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize Cognito client
cognito = boto3.client('cognito-idp')

# Cognito configuration
from GetCognitoCreds import get_secret
cognito_creds = get_secret()

USER_POOL_ID = cognito_creds['USER_POOL_ID']
CLIENT_ID = cognito_creds['CLIENT_ID']
CLIENT_SECRET = cognito_creds['CLIENT_SECRET']


def lambda_handler(event, context):
    try:
        # Load the attributes and check whether all the required inputs are sent
        body = json.loads(event['body'])
        email = body['email'].lower()
        password = body['password']
        first_name = body['firstName']
        last_name = body['lastName']
        terms_consent = body['hasTermsConsent']
        marketing_consent = body['hasMarketingConsent']
    except (KeyError, json.JSONDecodeError) as e:
        logger.error('Error processing body. Error: %s, with event: %s', e, event)  # log the error
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': str(e),
                'reason': 'InvalidBody' if isinstance(e, KeyError) else 'InvalidJson'
            })
        }
    except Exception as e:
        logger.error('Unknown error processing body. Error: %s, with event: %s', e, event)
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': str(e),
                'reason': 'Exception',
                'error': e
            })
        }

    except Exception as e:
        logger.error("Error validating inputs error: %s", e)

        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Server Error',
                'reason': 'Exception',
                'error': str(e)
            })
        }

    try:
        confirmation_method, destination = submit_cognito_sign_up(email, password, first_name, last_name)
        with Database() as database:
            user_id = log_sign_up(database, email)
            submit_agreements(database, user_id, marketing_consent, terms_consent)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'User successfully registered',
                'method': confirmation_method,
                'destination': destination
            })
        }
    except ClientError as e:
        error = e.response['Error']
        error_code = error['Code']
        logger.error('Client error: %s, with event %s', error, event)  # log the error
        if error_code in ['UsernameExistsException', 'InvalidPasswordException']:
            return {
                'statusCode': 401,
                'body': json.dumps({
                    'message': error['Message'],
                    'reason': 'CognitoException',
                    'error': error_code
                })
            }
        elif error_code == 'CodeDeliveryFailureException':
            return {
                'statusCode': 401,
                'body': json.dumps({
                    'message': error['Message'],
                    'reason': 'CognitoException',
                    'error': error_code
                })
            }
        elif error_code in ['InternalErrorException', 'TooManyRequestsException']:
            return {
                'statusCode': 401,
                'body': json.dumps({
                    'message': 'There has been a server issue, please try again',
                    'reason': 'CognitoException',
                    'error': error_code
                })
            }
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'message': error['Message'],
                    'reason': 'CognitoException',
                    'error': error_code
                })
            }
    except Exception as e:
        logger.error('Unknown error submitting cognito sign_up. Error: %s, with event: %s', e, event)
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': str(e),
                'reason': 'CognitoException',
                'error': str(e)
            })
        }


def submit_cognito_sign_up(email, password, first_name, last_name):
    """

    SignUp Docs:

    https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_SignUp.html

    """
    secret_hash = get_secret_hash(username=email, CLIENT_ID=CLIENT_ID, CLIENT_SECRET=CLIENT_SECRET)

    attributes = [
        {'Name': 'email', 'Value': email},
        {'Name': 'given_name', 'Value': first_name},
        {'Name': 'family_name', 'Value': last_name},
    ]

    response = cognito.sign_up(
        ClientId=CLIENT_ID,
        SecretHash=secret_hash,
        Username=email,
        Password=password,
        UserAttributes=attributes
    )

    delivery_details = response['CodeDeliveryDetails']

    confirmation_method = delivery_details['DeliveryMedium']
    destination = delivery_details['Destination']

    return confirmation_method, destination


def log_sign_up(database, email):

    response = cognito.list_users(
        UserPoolId=USER_POOL_ID,
        Filter="email=\"" + email + "\""
    )

    try:
        user_id = response['Users'][0]['Username']
    except (KeyError, IndexError) as e:
        logger.error('error logging sign up: ' + str(e))
        return
    except Exception as e:
        logger.error('error logging sign up: ' + str(e))
        return

    import time

    sql = "INSERT INTO SignUps(user_id, time) VALUES (%s, %s)"
    current_time = time.time()
    database.execute_insert_query(sql, (user_id, current_time))

    return user_id


def submit_agreements(database, user_id, marketingConsent, termsConsent):
    sql = "INSERT INTO Agreements(user_id, MarketingConsent, TermsConditions) VALUES (%s, %s, %s)"
    database.execute_insert_query(sql, (user_id, marketingConsent, termsConsent))
