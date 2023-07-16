"""

Logic for user signing in to platform

will take username and password from user and use the cognito initiate_auth to log in.
on a successful login it uses get_user

Response from cognito should be:

{
   "AuthenticationResult": {
      "AccessToken": "string",
      "ExpiresIn": number,
      "IdToken": "string",
      "NewDeviceMetadata": {
         "DeviceGroupKey": "string",
         "DeviceKey": "string"
      },
      "RefreshToken": "string",
      "TokenType": "string"
   },
   "ChallengeName": "string",
   "ChallengeParameters": {
      "string" : "string"
   },
   "Session": "string"
}

"""

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

    try:
        body = json.loads(event['body'])
        username = body['email'].lower()
        password = body['password']
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

        access_token = submit_cognito_initiate_auth(username, password)

    except SecretHashGenerationException:
        logger.error('Error generating secret hash with event: %s', event)  # log the error
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Error generating secret hash',
                'reason': 'SecretHashGenerator'
            })
        }

    except ClientError as e:
        error = e.response['Error']
        error_code = error['code']
        logger.error('Client error initiate_auth: %s, with event %s', error, event)  # log the error

        if error_code == 'UserNotConfirmedException':
            return {
                'statusCode': 401,
                'body': json.dumps({
                    'message': 'Account verification not yet complete',
                    'reason': 'CognitoException',
                    'error': error_code
                })
            }
        elif error_code == 'UserNotFoundException':
            return {
                'statusCode': 401,
                'body': json.dumps({
                    'message': 'Email is not associated with any account. Have you created an account?',
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
                'reason': 'Unknown'
            })
        }

    try:

        user_attributes = submit_cognito_get_user(access_token)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'User successfully logged in and attributes retrieved',
                'attributes': user_attributes
            })
        }

    except KeyError as e:
        logger.error('Error when getting attributes: %s', e)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': str(e),
                'reason': 'KeyErrorWhenGettingAttributes'
            })
        }
    except ClientError as e:
        error = e.response['Error']
        error_code = error['code']
        logger.error('Client error: %s, with event %s', error, event)  # log the error
        
        if error_code in ['InternalErrorException', 'TooManyRequestsException']:
            return {
                'statusCode': 401,
                'body': json.dumps({
                    'message': 'There has been a server issue, please try again',
                    'reason': 'InternalServerError'
                })
            }

    except Exception as e:
        logger.error('Unknown error submitting cognito sign_up. Error: %s, with event: %s', e, event)
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': str(e),
                'reason': 'Unknown'
            })
        }


def submit_cognito_initiate_auth(username, password):
    """

    InitiateAuth Docs:

    https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_InitiateAuth.html

    """

    secret_hash = get_secret_hash(username=username, CLIENT_ID=CLIENT_ID, CLIENT_SECRET=CLIENT_SECRET)

    response = cognito.initiate_auth(
        ClientId=CLIENT_ID,
        AuthFlow='USER_PASSWORD_AUTH',
        AuthParameters={
            'USERNAME': username,
            'PASSWORD': password,
            'SECRET_HASH': secret_hash
        }
    )

    access_token = response['AuthenticationResult']['AccessToken']

    return access_token


def submit_cognito_get_user(access_token):
    """

    Parameters
    ----------
    access_token - takes the access token provided by a cognito initiate auth

    Returns
    -------

    GetUser docs:

    https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_GetUser.html

    """

    response_data = cognito.get_user(
        AccessToken=access_token
    )
    """
        the following is used to change the returned attributes from the naming convention used by AWS
        and into our desired naming convention
    """

    mapping = {
        'email_verified': 'email_verified',
        'phone_number_verified': 'phone_number_verified',
        'phone_number': 'phone_number',
        'given_name': 'first_name',
        'family_name': 'surname',
        'email': 'email'
    }

    response = {
        'user_id': response_data['Username']
    }

    for attribute in response_data['UserAttributes']:
        name = attribute['Name']
        if name in mapping.keys():
            response[mapping[name]] = attribute['Value']

    return response
