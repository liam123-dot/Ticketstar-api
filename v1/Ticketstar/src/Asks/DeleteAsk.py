import pymysql
import json


def lambda_handler(event, context):

    try:

        body = json.loads(event['body'])

        ask_id = body['ask_id']

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

    with connection.cursor() as cursor:

        delete_query = "DELETE FROM Asks WHERE ask_id=%s"

        cursor.execute(delete_query, (ask_id, ))

        connection.commit()
        connection.close()

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': "Ask successfully deleted"
            })
        }
