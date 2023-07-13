import json
import pymysql
import time


def lambda_handler(event, context):
    try:
        data = json.loads(event['body'])
        ask_id = data['ask_id']
        buyer_user_id = data['user_id']

        if buyer_user_id is None:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'message': "No user id provided"
                })
            }

        print("reservation user id" + buyer_user_id)
    except KeyError:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': "Invalid body sent"
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

    with connection.cursor() as cursor:

        check_not_reserved_query = "SELECT reserved, buyer_user_id, reserve_timeout from asks WHERE ask_id=%s"

        cursor.execute(check_not_reserved_query, (ask_id, ))

        ask = cursor.fetchall()[0]

        current_time = int(time.time())

        if ask[0] == b'\x01' and ask[2] > current_time - 2:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'message': 'Listing has been reserved',
                    'reserver_user_id': ask[1],
                    'reserve_timeout': ask[2]
                })
            }

        reserve_timeout = current_time + 2 * 60

        fulfill_query = "UPDATE asks SET reserved = b'1', buyer_user_id=%s, reserve_timeout=%s WHERE ask_id=%s"

        cursor.execute(fulfill_query, (buyer_user_id, reserve_timeout, ask_id))

        connection.commit()
        connection.close()

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Successfully reserved',
                'reserve_timeout': str(reserve_timeout)
            })
        }

