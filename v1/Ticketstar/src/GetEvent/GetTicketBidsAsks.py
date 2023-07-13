import pymysql
import json


def lambda_handler(event, context):

    try:

        query_string_parameters = event['queryStringParameters']
        fixr_ticket_id = query_string_parameters['fixr_ticket_id']
        fixr_event_id = query_string_parameters['fixr_event_id']
        user_id = query_string_parameters['user_id']

    except KeyError:

        return {
            'statusCode': 400,
            'body': json.dumps({
                "message": "Invalid query string sent"
            })
        }

    try:
        data = get_bids_asks(fixr_ticket_id, fixr_event_id, user_id)
    except pymysql.err.OperationalError:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Error connecting to database'
            })
        }

    return {
        'statusCode': 200,
        'body': json.dumps(data)
    }


def get_bids_asks(fixr_ticket_id, fixr_event_id, user_id):
    try:

        connection = pymysql.connect(
            host="host.docker.internal",
            user='root',
            port=3306,
            password='Redyred358!',
            database='ticketstartest'
        )

    except pymysql.err.OperationalError:
        raise pymysql.err.OperationalError

    try:

        with connection.cursor() as cursor:
            query = "SELECT ticket_id FROM TICKETS WHERE fixr_ticket_id=%s AND fixr_event_id=%s"

            cursor.execute(query, (fixr_ticket_id, fixr_event_id))

            connection.commit()

            rows = cursor.fetchall()

            if len(rows) == 0:
                return {
                    'bid_count': 0,
                    'ask_count': 0
                }

            ticket_id = rows[0][0]

            bid_query = "SELECT bid_id, price from Bids WHERE ticket_id=%s AND fulfilled=0"

            cursor.execute(bid_query, (ticket_id,))

            bids_result = cursor.fetchall()

            ask_query = "SELECT ask_id, price, seller_user_id, reserved, reserve_timeout from Asks WHERE ticket_id=%s AND fulfilled=0 AND listed=1 ORDER BY price ASC"

            cursor.execute(ask_query, (ticket_id,))

            asks_result = cursor.fetchall()

            asks = []

            for ask in asks_result:
                asks.append({
                    'ask_id': ask[0],
                    'price': ask[1],
                    'user_id': ask[2],
                    'reserved': ask[3] == b'\x01',
                    'reserve_timeout': ask[4],
                })

            bids = []

            for bid in bids_result:
                bids.append({
                    'bid_id': bid[0],
                    'price': bid[1]
                })

            return_value = {

                'ask_count': len(asks),
                'bid_count': len(bids),
                'asks': asks,
                'bids': bids,

            }

            return return_value

    except Exception as e:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': "Unknown error: " + str(e)
            })
        }
