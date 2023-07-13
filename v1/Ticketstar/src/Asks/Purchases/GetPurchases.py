import json
import pymysql
from GetTransferUrl import get_transfer_url_from_real_ticket_id, check_ticket_been_transferred_from_real_ticket_id


def lambda_handler(event, context):

    try:
        queryStringParameters = event['queryStringParameters']
        user_id = queryStringParameters['user_id']
    except KeyError:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': "Invalid query string sent"
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
            get_purchases_query = "SELECT ask_id, price, ticket_id, real_ticket_id FROM asks WHERE fulfilled=1 AND buyer_user_id=%s"

            cursor.execute(get_purchases_query, (user_id, ))

            purchases = cursor.fetchall()

            response = {}

            for ticket in purchases:

                ask_id = ticket[0]
                price = ticket[1]
                ticket_id = ticket[2]
                real_ticket_id = ticket[3]

                get_ticket_info_query = "SELECT ticket_name, event_name, open_time, close_time, image_url, fixr_event_id, fixr_ticket_id from Tickets WHERE ticket_id=%s"

                cursor.execute(get_ticket_info_query, (ticket_id,))

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
                        'purchases': {}
                    }

                get_transfer_url_query = "SELECT ticket_transfer_url FROM realtickets WHERE real_ticket_id=%s"

                cursor.execute(get_transfer_url_query, (real_ticket_id, ))

                results = cursor.fetchall()

                if len(results) != 0 and results[0][0] is not None:

                    transfer_url = results[0][0]

                    if check_ticket_been_transferred_from_real_ticket_id(real_ticket_id):
                        transfer_url = None


                else:

                    transfer_url = None

                    if real_ticket_id is not None:

                        transfer_url = get_transfer_url_from_real_ticket_id(real_ticket_id)

                        if transfer_url is not None:

                            update_transfer_url_query = "UPDATE realtickets SET ticket_transfer_url=%s WHERE real_ticket_id=%s"

                            cursor.execute(update_transfer_url_query, (transfer_url, real_ticket_id))

                            connection.commit()

                response[fixr_event_id]['tickets'][fixr_ticket_id]['purchases'][ask_id] = {
                    'price': price,
                    'transfer_url': transfer_url,
                }

            connection.close()

            return {
                'statusCode': 200,
                'body': json.dumps(response)
            }

    except Exception as e:

        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Exception: ' + str(e)
            })
        }

    finally:
        try:
            connection.close()
        except Exception as e:
            pass
