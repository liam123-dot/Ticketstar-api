"""

Called when a seller goes to edit their listing, checks to make sure it is not currently reserved, should
reserve the listing for 2 minutes to prevent a buyer buying it in that time.

"""
import json
import logging
import time

import DatabaseException

logger = logging.getLogger()
logger.setLevel(logging.INFO)

from DatabaseActions import get_ask, reserve_ask
from DatabaseConnector import Database


def success(database, ask_id, seller_user_id):
    reserve_timeout = round(time.time() + 120)

    reserve_ask(database, ask_id, seller_user_id, reserve_timeout)

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'editable',
            'reserve_timeout': reserve_timeout
        })
    }


def lambda_handler(event, context):

    try:
        path_parameters = event['pathParameters']
        ask_id = path_parameters['ask_id']
    except KeyError as e:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Invalid query string parameters' + str(e)
            })
        }

    with Database() as database:

        try:

            ask = get_ask(database, ask_id)

        except DatabaseException.DatabaseException as e:
            logger.error("Database error: %s", str(e))
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'message': 'Server error'
                })
            }

        if ask['fulfilled']:
            return {
                'statusCode': 401,
                'body': json.dumps({
                    'message': 'Listing has been purchased'
                })
            }

        seller_user_id = ask['seller_user_id']
        if ask['reserved']:
            current_time = round(time.time())
            if ask['reserve_timeout'] < current_time:
                editable = True
            elif ask['buyer_user_id'] == seller_user_id:
                editable = True
            else:
                return {
                    'statusCode': 401,
                    'body': json.dumps({
                        'message': 'Cannot edit, listing is currently reserved'
                    })
                }

        else:
            editable = True

        if editable:
            return success(database, ask_id, seller_user_id)

