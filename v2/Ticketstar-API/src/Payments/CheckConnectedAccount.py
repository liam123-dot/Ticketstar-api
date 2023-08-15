
"""

Function that will take a user id and check if they have a connected account.
If they do, it will check to make sure it is valid to receive funds

"""
import json
from DatabaseConnector import Database
import logging
import stripe

logger = logging.getLogger()
logger.setLevel(logging.INFO)

secret_key = "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"
publishable_key = "pk_live_51NJwFSDXdklEKm0RH9UR7RgQ2kPsEQvbFaSJKVl5PnBMNWVIVT88W4wMIo8IIm9A6TvKOBOVV4xPSN9tvPMHAZOJ00uA9XSbKi"

secret_key = "sk_test_51NJwFSDXdklEKm0RDJhFhwEBcJLEPOtBtdeovg18JHIIu4HxkXLge19WAPvUap3V0drBuJOgrvccYNgCFaLfsW3x00ME3KwKgi"
publishable_key = "pk_test_51NJwFSDXdklEKm0R8JRHkohXh2qEKG57G837zZCKOUFXlyjTNkHa2XOSUa0zhN2rQaVkd9NPTykrdC9IRnoBlZ7Z00uMUWz549"


def lambda_handler(event, context):

    try:
        body = json.loads(event['body'])
        user_id = body['user_id']
    except KeyError as e:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Invalid parameters, ' + str(e)
            })
        }
    except json.JSONDecoder as e:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Invalid body sent, ' + str(e)
            })
        }

    try:
        with Database() as database:
            sql_query = "SELECT seller_id FROM stripe WHERE user_id=%s"
            results = database.execute_select_query(sql_query, (user_id, ))

            if len(results) == 0 or results[0][0] is None:
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'user_has_stripe': False,
                        'further_action_required': False
                    })
                }
            else:

                seller_id = results[0][0]

                further_action_required = check_stripe_account_enabled(seller_id)

                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'user_has_stripe': True,
                        'further_action_required': further_action_required
                    })
                }

    except Exception as e:
        logger.error(type(e))
        logger.error("Error checking if seller enable: %s", str(e))
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Internal error'
            })
        }

def check_stripe_account_enabled(seller_id):
    stripe.api_key = secret_key

    account = stripe.Account.retrieve(seller_id)

    logger.info(json.dumps(account, indent=4))

    further_action_required = account['requirements']['disabled_reason'] is not None

    return further_action_required
