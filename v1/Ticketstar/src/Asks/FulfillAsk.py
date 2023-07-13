import json
import pymysql


def lambda_handler(event, context):

    try:
        data = json.loads(event['body'])
        ask_id = data['ask_id']
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

    try:

        with connection.cursor() as cursor:

            fulfill_query = "UPDATE asks SET fulfilled = b'1', reserve_timeout=NULL WHERE ask_id=%s"

            cursor.execute(fulfill_query, (ask_id, ))

            connection.commit()
            connection.close()

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Ask successfully fulfilled!'
            })
        }

    except Exception as e:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Error: ' + str(e)
            })
        }