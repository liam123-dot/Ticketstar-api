
"""

This lambda function is called after the user has a verified transfer url/pdf.

If it is a transfer url:

The claim_ticket function will be written. This function is in the TransferUrl.py in the FixrFunctions
layer.

"""
import json
from TransferURL import claim_ticket
from DatabaseActions import check_relationship_exists, get_ticket_id, create_new_relationship, create_real_ticket, create_ask
from DatabaseException import DatabaseException
from GeneralFixrUtils import get_ticket_max
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):

    try:

        body = json.loads(event['body'])
        fixr_ticket_id = body['fixr_ticket_id']
        fixr_event_id = body['fixr_event_id']
        transfer_url = body['transfer_url']
        price = body['price']
        user_id = body['user_id']

    except json.JSONDecodeError as e:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Invalid body sent',
                'reason': 'InvalidBodyJson'
            })
        }
    except KeyError as e:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Missing or incorrect body item: ' + str(e),
                'reason': 'KeyError'
            })
        }

    try:

        ticket_id = get_ticket_id(fixr_event_id, fixr_ticket_id)

        try:

            account_id, ticket_reference = claim_ticket(transfer_url, ticket_id)

        except Exception:
            return {
                'statusCode': 401,
                'body': json.dumps({
                    'message': "Error claiming transfer url, please check it is still valid",
                    'reason': 'TransferURL'
                })
            }

        relationship_exists = check_relationship_exists(account_id, ticket_id)

        if not relationship_exists:
            max_per_user = get_ticket_max(fixr_event_id, fixr_ticket_id)
            create_new_relationship(account_id, ticket_id, max_per_user)

        real_ticket_id = create_real_ticket(ticket_id, account_id, ticket_reference)
        create_ask(user_id, price, real_ticket_id, ticket_id)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Ask successfully created'
            })
        }

    except DatabaseException as e:
        logger.error("Database error when posting ask, error: %s", e)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Internal Server Error'
            })
        }
    except Exception as e:
        logger.error("Exception when posting ask, error: %s", e)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Internal Server Error'
            })
        }
