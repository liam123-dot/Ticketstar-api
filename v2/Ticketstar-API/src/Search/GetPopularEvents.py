import json

from DatabaseConnector import Database
from DatabaseActions import check_event_has_tickets

import logging
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
                'message': 'Invalid parameter: ' + str(e)
            })
        }

    sql = """
        SELECT event_id, COUNT(*) AS count
        FROM EventSearches
        WHERE time > (UNIX_TIMESTAMP(NOW()) - 86400)
        GROUP BY event_id
        ORDER BY count DESC
        LIMIT 5;
    """
    with Database() as database:
        results = database.execute_select_query(sql, ())

        response = []

        for event_id in results:
            try:
                event_id = event_id[0]
                sql = """
                    SELECT event_name, image_url, open_time, close_time, venue_name
                    FROM tickets
                    WHERE fixr_event_id=%s            
                """

                results = database.execute_select_query(sql, (event_id, ))[0]

                response.append({
                    'fixr_id': event_id,
                    'name': results[0],
                    'image_url': results[1],
                    'open_time': results[2],
                    'close_time': results[3],
                    'venue': results[4],
                    'has_listings': check_event_has_tickets(database, event_id, user_id)
                })
            except Exception as e:
                logger.error(str(e))

    return {
        'statusCode': 200,
        'body': json.dumps({
            'events': response
        })
    }
