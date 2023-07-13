import pymysql
import json
from UpdateTicketData import update


def lambda_handler(event, context):

    '''
    Function that is called when a buyer posts an asking price for a ticket. Used if the buyer isn't insta-buying.
    :param event:

        requires a body key with
        :param body:

            user_id
            fixr_ticket_id
            fixr_event_id
            price


    :param context:
    :return:
    '''

    try:

        body = json.loads(event['body'])

        user_id = body['user_id']
        fixr_ticket_id = body['fixr_ticket_id']
        fixr_event_id = body['fixr_event_id']
        price = float(body['price'])
        real_ticket_id = int(body['real_ticket_id'])

        if user_id is None:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'message': 'No user id sent'
                })
            }

    except KeyError:

        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': "Invalid body type"
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

            get_ticket_id_query = "SELECT ticket_id FROM tickets WHERE fixr_ticket_id=%s AND fixr_event_id=%s"

            cursor.execute(get_ticket_id_query, (fixr_ticket_id, fixr_event_id))

            ticket_id_result = cursor.fetchall()

            if len(ticket_id_result) == 0:
                create_ticket_query = "INSERT INTO tickets(fixr_ticket_id, fixr_event_id) values(%s,%s)"

                cursor.execute(create_ticket_query, (fixr_ticket_id, fixr_event_id))

                connection.commit()

                update()

                get_ticket_id_query = "SELECT ticket_id FROM tickets WHERE fixr_ticket_id=%s AND fixr_event_id=%s"

                cursor.execute(get_ticket_id_query, (fixr_ticket_id, fixr_event_id))

                ticket_id_result = cursor.fetchall()

            post_ask_query = "INSERT INTO asks(price, ticket_id, seller_user_id, fulfilled, real_ticket_id) values(%s,%s,%s,0, %s)"

            ticket_id = ticket_id_result[0][0]

            cursor.execute(post_ask_query, (price, ticket_id, user_id, real_ticket_id))

            connection.commit()

        return {
            'statusCode': 200,
            "body": json.dumps({
                "message": "Ask successfully added"
            })
        }

    except Exception as e:
        connection.close()

        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Unknown Error Exception: ' + str(e)
            })
        }
