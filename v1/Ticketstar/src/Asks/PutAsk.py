import pymysql
import json
import os


def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        price = float(body['price'])
        ask_id = int(body['ask_id'])

    except KeyError:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'message': "Invalid body type"})
        }

    connection = None

    try:
        connection = pymysql.connect(
            host="host.docker.internal",
            user='root',
            port=3306,
            password='Redyred358!',
            database='ticketstartest'
        )

        with connection.cursor() as cursor:
            update_query = "UPDATE Asks SET price=%s WHERE ask_id=%s"
            cursor.execute(update_query, (price, ask_id))
            connection.commit()

        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'message': 'Successfully edited ask'})
        }

    except pymysql.err.OperationalError:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'message': "Error whilst connecting to database"})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'message': 'An error occurred', 'error': str(e)})
        }
    finally:
        if connection:
            connection.close()
