"""

Small function that is used to set listed from 0 to 1 of unlisted items

"""

import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

from DatabaseActions import relist_listing
from DatabaseException import DatabaseException

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
        relist_listing(ask_id)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'listing successfully relisted'
            })
        }

    except DatabaseException as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'body': "server error"
            })
        }

