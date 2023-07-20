"""

'Deletes' a listing, will set listed=0. If an account has listed=0 on it's listing screen should have link
for transfer url

"""
import json
from DatabaseActions import remove_listing
from DatabaseException import DatabaseException
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):

    try:
        body = json.loads(event['body'])

        ask_id = body['ask_id']

    except KeyError as e:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Invalid requests parameters: ' + str(e)
            })
        }

    try:
        remove_listing(ask_id)
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Listing successfully removed'
            })
        }
    except DatabaseException as e:
        logger.error("database error when removing listing, error: %s", e)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Server error'
            })
        }
