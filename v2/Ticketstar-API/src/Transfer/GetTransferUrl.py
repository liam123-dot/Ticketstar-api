
"""

Takes ask id as path parameter and gets the transfer url for that event

"""
import json

from DatabaseActions import get_real_ticket_by_ask_id, get_fixr_account_details_from_account_id
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
