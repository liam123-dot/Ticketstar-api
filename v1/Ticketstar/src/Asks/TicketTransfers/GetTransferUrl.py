import json
import requests
import pymysql


def lambda_handler(event, context):

    try:
        data = json.loads(event['queryStringParameters'])

        real_ticket_id = data['real_ticket_id'] # where actual ticket is stored in system along with fixr username/password

    except KeyError:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Invalid query string sent'
            })
        }

    transfer_url = get_transfer_url_from_real_ticket_id(real_ticket_id)

    return {
        'statusCode': 200,
        'body': json.dumps({
            'transfer_url': transfer_url
        })
    }


def login(session, username, password):
    login_url = "https://api.fixr.co/api/v2/app/user/authenticate/with-email"

    login_body = {
        'email': username,
        'password': password
    }

    login_response = session.post(login_url, json=login_body)

    data = login_response.json()

    auth_token = data['auth_token']

    return auth_token


def get_ticket_reference(session, auth_token, fixr_ticket_id, fixr_event_id):
    get_bookings_url = "https://api.fixr.co/api/v2/app/booking?only=future&limit=999"

    get_bookings_headers = {
        'Accept': 'application/json',
        'Authorization': 'Token ' + auth_token
    }

    response = session.get(get_bookings_url, headers=get_bookings_headers)

    data = response.json()

    for event in data['data']:
        if event['event']['id'] == fixr_event_id and event['ticket_type']['id'] == fixr_ticket_id:
            return event['reference_id']


def get_transfer_url(session, auth_token, ticket_reference):
    create_transfer_code_url = f"https://api.fixr.co/api/v2/app/booking/{ticket_reference}/transfer-code"

    get_bookings_headers = {
        'Accept': 'application/json',
        'Authorization': 'Token ' + auth_token
    }

    data = {
        'note': ''
    }

    response = session.post(create_transfer_code_url, headers=get_bookings_headers, json=data)

    data = response.json()

    transfer_url = data['transfer_url']

    return transfer_url


def get_transfer_url_from_ask(ask_id):
    connection = pymysql.connect(
        host="host.docker.internal",
        user='root',
        port=3306,
        password='Redyred358!',
        database='ticketstartest'
    )

    with connection.cursor() as cursor:

        get_real_ticket_id_query = "SELECT real_ticket_id FROM asks WHERE ask_id=%s"

        cursor.execute(get_real_ticket_id_query, (ask_id, ))

        result = cursor.fetchall()

        if len(result) == 0:
            return

        real_ticket_id = result[0][0]

    transfer_url = get_transfer_url_from_real_ticket_id(real_ticket_id)

    connection.close()

    return transfer_url


def get_transfer_url_from_real_ticket_id(real_ticket_id):
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

        get_real_ticket_details_query = "SELECT fixr_username, fixr_password, fixr_ticket_reference FROM realtickets WHERE real_ticket_id=%s"

        cursor.execute(get_real_ticket_details_query, (real_ticket_id, ))

        result = cursor.fetchall()

        if len(result) == 0:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'message': 'real ticket id doesn\'t exist'
                })
            }

        real_ticket = result[0]

        fixr_username = real_ticket[0]
        fixr_password = real_ticket[1]
        ticket_reference = real_ticket[2]

        with requests.Session() as s:
            auth_token = login(s, fixr_username, fixr_password)
            transfer_url = get_transfer_url(s, auth_token, ticket_reference)

    connection.commit()
    connection.close()

    return transfer_url


def get_transfer_url_from_details(fixr_username, fixr_password, ticket_reference):
    with requests.Session() as s:
        auth_token = login(s, fixr_username, fixr_password)
        transfer_url = get_transfer_url(s, auth_token, ticket_reference)

    return transfer_url