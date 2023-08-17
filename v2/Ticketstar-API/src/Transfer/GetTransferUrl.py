
"""

Takes ask id as path parameter and gets the transfer url for that event

"""
import json

from DatabaseActions import get_real_ticket_by_ask_id, get_fixr_account_details_from_account_id
from DatabaseConnector import Database
from DatabaseException import DatabaseException
from FixrExceptions import FixrApiException
from TransferURL import get_transfer_url
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):

    try:

        path_parameters = event['pathParameters']
        ask_id = path_parameters['ask_id']

        body = json.loads(event['body'])
        user_id = body['user_id']

        authorized = confirm_ticket_ownership(user_id, ask_id)

        if not authorized:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'message': 'Unauthorized',
                    'reason': 'TicketNoLongerAvailable'
                })
            }

    except KeyError as e:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Invalid parameters: ' + str(e)
            })
        }

    try:

        transfer_url = get_transfer_url_from_ask(ask_id)

    except DatabaseException as e:
        logger.error("Database exception: %s", e)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Internal Server Error'
            })
        }
    except FixrApiException as e:
        logger.error("Fixr API exception: %s", e)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Internal Server Error'
            })
        }

    return {
        'statusCode': 200,
        'body': json.dumps({
            'transfer_url': transfer_url
        })
    }


def get_transfer_url_from_ask(ask_id):
    real_ticket = get_real_ticket_by_ask_id(ask_id)

    account_id = real_ticket[0]
    ticket_reference = real_ticket[1]

    account_details = get_fixr_account_details_from_account_id(account_id)[0]

    fixr_username = account_details[0]
    fixr_password = account_details[1]

    transfer_url = get_transfer_url(fixr_username, fixr_password, ticket_reference)

    return transfer_url


def confirm_ticket_ownership(user_id, ask_id):

    with Database() as database:
        sql = "SELECT fulfilled, seller_user_id, buyer_user_id, listed FROM asks WHERE ask_id=%s"

        results = database.execute_select_query(sql, (ask_id, ))[0]

    fulfilled = results[0] == b'\x01'
    seller_user_id = results[1]
    buyer_user_id = results[2]
    listed = results[3] == b'\x01'

    if fulfilled:
        if buyer_user_id == user_id:
            return True
        else:
            return False
    else:
        if seller_user_id == user_id:
            if listed:
                return False
            return True
        else:
            return False

