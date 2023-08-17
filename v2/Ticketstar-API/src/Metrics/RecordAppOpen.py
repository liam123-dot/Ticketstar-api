# called when the app is opened.
import json
import time
import logging
from DatabaseConnector import Database

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):

    try:
        body = json.loads(event['body'])
        user_id = body['user_id']

    except KeyError as e:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Error with key: ' + str(e)
            })
        }
    except json.JSONDecodeError as e:
        logger.error('Error decoding json: %s, event: %s', e, event)
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'error decoding json: ' + str(e)
            })
        }

    try:

        with Database() as database:
            current_time = time.time()
            sql = "INSERT INTO Sessions(user_id, open_time) VALUES(%s, %s)"

            database.execute_insert_query(sql, (user_id, current_time))

            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Success'
                })
            }

    except Exception as e:
        logger.error('Error logging app open: %s, event: ', str(e), event)
