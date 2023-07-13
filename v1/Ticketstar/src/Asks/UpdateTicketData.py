import pymysql
import requests
import json


def update():
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

    with connection.cursor() as cursor:

        get_tickets_query = "SELECT ticket_id, fixr_ticket_id, fixr_event_id FROM Tickets WHERE image_url is NULL"

        cursor.execute(get_tickets_query)

        ticket_ids = cursor.fetchall()

        for i in range(0, len(ticket_ids)):
            ticket = ticket_ids[i]
            ticket_id = ticket[0]
            fixr_ticket_id = ticket[1]
            fixr_event_id = ticket[2]

            get_event_url = f"https://api.fixr.co/api/v2/app/event/{fixr_event_id}?"

            response = requests.get(get_event_url)

            if response.ok:
                data = response.json()

                event_name = data['name']
                open_time = data['open_time']
                close_time = data['close_time']
                image_url = data['event_image']
                ticket_name = ""

                for ticket in data['tickets']:
                    if ticket['id'] == fixr_ticket_id:
                        ticket_name = ticket['name']

                update_ticket_query = "UPDATE Tickets SET ticket_name=%s, event_name=%s, open_time=%s, close_time=%s, image_url=%s where ticket_id=%s"

                cursor.execute(update_ticket_query, (ticket_name, event_name, open_time, close_time, image_url, ticket_id))

                connection.commit()
                connection.close()

