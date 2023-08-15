
"""

function is called when a user clicks buy.

It must handle many functions.

It also checks to confirm that the price has not changed, i.e listing has not been altered in between
refreshes of their apps data

If there is currently a reservation:

    1. check if it is the current user who already has a reservation:
        if so: 200, reset the timer
        else: 400, already reserved
    2. the timer has passed: 200, reset time for new buyer
    3. the ask has been fulfilled: 400,

otherwise:

    set reserved=1
    set buyer_user_id = user_d
    set reserve

post function that takes the ask_id, user_id and price

"""

import json
import logging
import time
from DatabaseActions import get_ask
from DatabaseActions import reserve_ask as database_reserve_ask
from DatabaseConnector import Database
from DatabaseException import DatabaseException

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    try:
        # Load the attributes and check whether all the required inputs are sent
        body = json.loads(event['body'])
        ask_id = body['ask_id']
        user_id = body['user_id']
        price = body['price']
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

    with Database() as database:

        try:

            ask = get_ask(database, ask_id)

        except DatabaseException as e:
            logger.error("Error getting ask, error: %s", str(e))
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'message': 'database exception',
                    'reason': 'DatabaseException'
                })
            }

        if price != ask['price']:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'message': 'price has been changed',
                    'reason': 'AskUpdated'
                })
            }

        current_time = time.time()

        try:

            if ask['seller_user_id'] == user_id:
                return {
                    'statusCode': 400,
                    'body': json.dumps({
                        'message': 'Listing can not be purchased by seller',
                        'reason': 'NotPurchasableBySeller'
                    })
                }

            if ask['fulfilled']:
                return {
                    'statusCode': 400,
                    'body': json.dumps({
                        'message': "listing has been fulfilled",
                        'reason': 'ListingFulfilled'
                    })
                }
            if ask['reserved']:
                if ask['buyer_user_id'] == user_id:
                    return reserve_ask(database, ask_id, user_id)
                elif ask['reserve_timeout'] < current_time:
                    return reserve_ask(database, ask_id, user_id)
                else:
                    return {
                        'statusCode': 400,
                        'body': json.dumps({
                            'message': 'listing has been reserved',
                            'reason': 'ListingReserved'
                        })
                    }

            return reserve_ask(database, ask_id, user_id)

        except DatabaseException as e:
            logger.error("Error getting ask, error: %s", str(e))
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'message': 'database exception',
                    'reason': 'DatabaseException'
                })
            }
        except Exception as e:
            logger.error("Error returning ask information, error: %s", str(e))
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'message': 'unknown exception',
                    'reason': 'Exception'
                })
            }

def reserve_ask(database, ask_id, user_id):
    reserve_timeout = round(time.time() + 120)
    database_reserve_ask(database, ask_id, user_id, reserve_timeout)

    return {
        'statusCode': 200,
        'body': json.dumps({
            'reserve_timeout': reserve_timeout
        })
    }
