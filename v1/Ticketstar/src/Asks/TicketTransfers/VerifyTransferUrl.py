import json
import requests
import pymysql
from GetTransferUrl import get_transfer_url_from_details, get_ticket_reference


def lambda_handler(event, context):

    # return {'statusCode': 200, 'body': json.dumps({'real_ticket_id': 1})}

    try:
        body = json.loads(event['body'])

        transfer_url = body['transfer_url']
        fixr_ticket_id = int(body['fixr_ticket_id'])
        fixr_event_id = int(body['fixr_event_id'])
        user_id = body['user_id']

    except KeyError:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Invalid Body'
            })
        }

    get_fixr_account_query = """
        SELECT fa.fixr_username, fa.fixr_password, fa.account_id
        FROM fixraccounts fa
        LEFT JOIN currentAccountRelationships car ON fa.account_id = car.account_id
        WHERE car.account_id IS NULL OR car.ticket_id != %s OR car.quantity < car.ticket_limit
    """

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

            ticket_id = ticket_id_result[0][0]

            cursor.execute(get_fixr_account_query, (ticket_id, ))

            result = cursor.fetchone()

            while True:

                fixr_account_email = result[0]
                fixr_account_password = result[1]
                fixr_account_id = result[2]

                login_url = "https://api.fixr.co/api/v2/app/user/authenticate/with-email"

                login_body = {
                    'email': fixr_account_email,
                    'password': fixr_account_password
                }

                with requests.Session() as s:
                    login_response = s.post(login_url, json=login_body)

                    data = login_response.json()

                    auth_token = data['auth_token']

                    verify_transfer_headers = {
                        'Accept': 'application/json',
                        'Authorization': 'Token ' + auth_token
                    }

                    code = transfer_url.split("/")[-1]

                    verify_transfer_url = "https://api.fixr.co/api/v2/app/transfer-ticket/" + code

                    response = s.post(verify_transfer_url, headers=verify_transfer_headers, json={})
                    data = response.json()

                    if not response.ok:
                        if data['message'] == "They are already your tickets! You can cancel your transfer from your profile if you have changed your mind and still want them.":
                            result = cursor.fetchone()
                        else:
                            return {
                                'statusCode': 400,
                                'body': json.dumps({
                                    'message': 'There was an error with validating the ticket'
                                })
                            }
                    else:


                        try:

                            _ticket_id = data['data']['ticket_reference']['ticket_type']['id']
                            _event_id = data['data']['ticket_reference']['event']['id']
                            break

                        except KeyError:
                            print(json.dumps(data, indent=4))

                        if not (_ticket_id == fixr_ticket_id and _event_id == fixr_event_id):
                            return {
                                'statusCode': 400,
                                'body': json.dumps({
                                    'message': 'Invalid transfer url for selected event'
                                })
                            }

            try:

                max_per_user = get_ticket_max(_event_id, _ticket_id)

            except Exception as e:
                return {
                    'statusCode': 400,
                    'body': json.dumps({
                        'error': str(e),
                        'process': 'max_per_user'
                    })
                }

            try:

                create_relationship_query = "INSERT INTO currentAccountRelationships(ticket_id, account_id, quantity, ticket_limit) VALUES(%s, %s, 1, %s)"

                cursor.execute(create_relationship_query, (ticket_id, fixr_account_id, max_per_user))

                connection.commit()

            except Exception as e:
                return {
                    'statusCode': 400,
                    'body': json.dumps({
                        'error': str(e),
                        'process': 'create relationship'
                    })
                }

            try:

                ticket_reference = get_ticket_reference(s, auth_token, fixr_ticket_id, fixr_event_id)

            except Exception as e:
                return {
                    'statusCode': 400,
                    'body': json.dumps({
                        'error': str(e),
                        'process': 'get ticket reference'
                    })
                }

            try:

                new_transfer_url = get_transfer_url_from_details(fixr_account_email, fixr_account_password, ticket_reference)

            except Exception as e:
                return {
                    'statusCode': 400,
                    'body': json.dumps({
                        'error': str(e),
                        'process': 'get new ticket transfer url'
                    })
                }

            try:

                add_real_ticket_query = "INSERT INTO realtickets(fixr_username, fixr_password, ticket_id, user_id, fixr_ticket_reference, ticket_transfer_url) VALUES (%s, %s, %s, %s, %s, %s)"

                cursor.execute(add_real_ticket_query, (fixr_account_email, fixr_account_password, ticket_id, user_id, ticket_reference, new_transfer_url))

                connection.commit()

            except Exception as e:
                return {
                    'statusCode': 400,
                    'body': json.dumps({
                        'error': str(e),
                        'process': 'add real ticket'
                    })
                }

            try:

                get_real_ticket_id_query = "SELECT real_ticket_id FROM RealTickets WHERE fixr_username=%s AND fixr_password=%s AND ticket_id=%s AND user_id=%s"

                cursor.execute(get_real_ticket_id_query, (fixr_account_email, fixr_account_password, ticket_id, user_id))

                real_ticket_id = cursor.fetchall()[0][0]

                connection.commit()

            except Exception as e:
                return {
                    'statusCode': 400,
                    'body': json.dumps({
                        'error': str(e),
                        'process': 'get real ticket id'
                    })
                }
            connection.close()

            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Ticket successfully verified',
                    'real_ticket_id': real_ticket_id
                })
            }
    except Exception as e:
        return {
            'statusCode': 400,
            'body': json.dumps(str(e))
        }


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


def get_ticket_max(event_id, ticket_id):
    get_event_info_url = f"https://api.fixr.co/api/v2/app/event/{event_id}"

    response = requests.get(get_event_info_url)
    data = response.json()

    for ticket in data['tickets']:
        if ticket['id'] == ticket_id:
            return ticket['max_per_user']
