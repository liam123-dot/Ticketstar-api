
"""

Takes ask id as path parameter and gets the transfer url for that event

"""
import json

from DatabaseActions import get_real_ticket_by_ask_id, get_fixr_account_details_from_account_id
from TransferURL import get_transfer_url

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

    real_ticket = get_real_ticket_by_ask_id(ask_id)

    account_id = real_ticket[0]
    ticket_reference = real_ticket[1]

    account_details = get_fixr_account_details_from_account_id(account_id)[0]

    fixr_username = account_details[0]
    fixr_password = account_details[1]

    transfer_url = get_transfer_url(fixr_username, fixr_password, ticket_reference)

    return {
        'statusCode': 200,
        'body': json.dumps({
            'transfer_url': transfer_url
        })
    }

