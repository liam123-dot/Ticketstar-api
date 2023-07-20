import json

from DatabaseActions import edit_listing
from DatabaseException import DatabaseException

def lambda_handler(event, context):

    try:
        body = json.loads(event['body'])

        ask_id = body['ask_id']
        price = body['price']

    except KeyError as e:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Invalid requests parameters: ' + str(e)
            })
        }

    try:
        edit_listing(ask_id, price)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Ask successfully edited'
            })
        }

    except DatabaseException as e:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Server error'
            })
        }

