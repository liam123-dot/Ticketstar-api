
"""

Function calls the fixr functions layer to verify a transfer url

"""
import json

import FixrExceptions
from TransferURL import verify_transfer_url
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):

    try:

        body = json.loads(event['body'])
        transfer_url = body['transfer_url']
        fixr_event_id = body['fixr_event_id']
        fixr_ticket_id = body['fixr_ticket_id']

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

        transfer_url_correct = verify_transfer_url(transfer_url, fixr_event_id, fixr_ticket_id)

        if transfer_url_correct:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': "Transfer url valid"
                })
            }
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'message': 'Invalid transfer url'
                })
            }

    except FixrExceptions.FixrApiException as e:
        logger.error("FixrAPI error when verifying a transferURL, transfer_url: %s, error: %s", transfer_url, str(e))
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': "Server error"
            })
        }
    except Exception as e:
        logger.error("Error when verifying transfer url, transfer_url: %s, error: %s", transfer_url, str(e))
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Server Error'
            })
        }
