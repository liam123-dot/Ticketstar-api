import json
import pymysql


def lambda_handler(event, context):

    # takes in a user id and returns all the asks that they have posted

    try:
        queryStringParameters = event['queryStringParameters']
    except KeyError:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'No query string parameters provided'
            })
        }

    try:
        user_id = queryStringParameters['user_id']

        if user_id is None:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'message': 'No user id provided'
                })
            }

    except KeyError:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'No user id provided'
            })
        }

    try:

        connection = pymysql.connect(
            host="host.docker.internal",
            user='root',
            port=3306,
            password='Redyred358!',
            database='ticketstartest'
        )

    except pymysql.err.OperationalError:

        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': "Error whilst connecting to database"
            })
        }

    try:

        with connection.cursor() as cursor:

            get_asks_query = "SELECT ask_id, price, ticket_id, fulfilled, reserved FROM Asks WHERE seller_user_id=%s"

            cursor.execute(get_asks_query, (user_id, ))

            asks = cursor.fetchall()

            response = {}

            for ask in asks:

                ask_id = ask[0]
                price = ask[1]
                ticket_id = ask[2]
                fulfilled = ask[3] == b'\x01'
                reserved = ask[4] == b'\x01'

                get_ticket_info_query = "SELECT ticket_name, event_name, open_time, close_time, image_url, fixr_event_id, fixr_ticket_id from Tickets WHERE ticket_id=%s"

                cursor.execute(get_ticket_info_query, (ticket_id, ))

                ticket_info = cursor.fetchall()[0]

                ticket_name = ticket_info[0]
                event_name = ticket_info[1]
                open_time = ticket_info[2]
                close_time = ticket_info[3]
                image_url = ticket_info[4]
                fixr_event_id = ticket_info[5]
                fixr_ticket_id = ticket_info[6]

                if fixr_event_id not in response.keys():
                    response[fixr_event_id] = {
                        'event_name': event_name,
                        'image_url': image_url,
                        'open_time': open_time,
                        'close_time': close_time,
                        'tickets': {}
                    }

                if fixr_ticket_id not in response[fixr_event_id]['tickets'].keys():
                    response[fixr_event_id]['tickets'][fixr_ticket_id] = {
                        'ticket_name': ticket_name,
                        'ticket_id': ticket_id,
                        'asks': {}
                    }

                response[fixr_event_id]['tickets'][fixr_ticket_id]['asks'][ask_id] = {
                    'price': price,
                    'fulfilled': fulfilled,
                    'reserved': reserved
                }

            connection.close()

            return {
                'statusCode': 200,
                'body': json.dumps(response)
            }

    except Exception as e:
        try:
            connection.close()
        except:
            pass

        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Unknown Error\nException: ' + str(e)
            })
        }
