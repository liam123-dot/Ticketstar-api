"""

Function to fulfill an ask once payment has been confirmed
add some confirmation about making sure the reserver and buyer are the same

"""
import json
import logging
import time

import DatabaseException
from DatabaseActions import get_ask, fulfill_listing

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):

    try:
        body = json.loads(event['body'])
        buyer_user_id = body['buyer_user_id']
        ask_id = body['ask_id']
    except json.JSONDecoder as e:
        logger.error("Error decoding body json, error: %s", str(e))
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Invalid body sent, json error'
            })
        }
    except KeyError as e:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': f"Invalid body sent, error: {e}"
            })
        }

    ask_info = get_ask(ask_id)

    if ask_info['reserved']:

        if ask_info['buyer_user_id'] != buyer_user_id:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'message': 'Reserve timed out, listing been reserved by another user'
                })
            }

    if ask_info['fulfilled']:
        if ask_info['buyer_user_id'] != buyer_user_id:
            return {
                'statusCode': 401,
                'body': json.dumps({
                    'message': 'Listing no longer available'
                })
            }
        elif ask_info['buyer_user_id'] == buyer_user_id:
            return {
                'statusCode': 401,
                'body': json.dumps({
                    'message': 'You have already bought this ticket'
                })
            }

    try:

        fulfill_listing(buyer_user_id, ask_id)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Listing successfully fulfilled'
            })
        }

    except DatabaseException.DatabaseException as e:
        logger.error("Database error when fulfilling ask: %s", str(e))
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'internal server error'
            })
        }



