import json
import pymysql
import stripe as stripe


def lambda_handler(event, context):

    try:
        body_data = json.loads(event['body'])
    except KeyError:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'No body provided'
            })
        }

    try:
        price = int(float(body_data['price']) * 100)
        user_email = body_data['user_email']
        user_id = body_data['user_id']
        user_phone_number = body_data['user_phone_number']
        user_name = body_data['user_name']

    except KeyError:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Missing a parameter'
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

    stripe.api_key = 'sk_test_51NJwFSDXdklEKm0RDJhFhwEBcJLEPOtBtdeovg18JHIIu4HxkXLge19WAPvUap3V0drBuJOgrvccYNgCFaLfsW3x00ME3KwKgi'

    with connection.cursor() as cursor:
        get_customer_id_query = "SELECT customer_id from stripe WHERE user_id=%s"

        cursor.execute(get_customer_id_query, (user_id, ))

        results = cursor.fetchall()

        if len(results) == 0:
            new_customer = stripe.Customer.create(
                name=user_name,
                email=user_email,
                phone=user_phone_number,
            )

            customer_id = new_customer['id']

            post_customer_id_query = "INSERT INTO stripe(user_id, customer_id) VALUES(%s, %s)"

            cursor.execute(post_customer_id_query, (user_id, customer_id))

        else:
            customer_id = results[0][0]

        connection.commit()
        connection.close()

    # Set your secret key. Remember to switch to your live secret key in production.
    # See your keys here: https://dashboard.stripe.com/apikeys
    # Use an existing Customer ID if this is a returning customer


    ephemeralKey = stripe.EphemeralKey.create(
    customer=customer_id,
    stripe_version='2022-11-15',
    )
    paymentIntent = stripe.PaymentIntent.create(
    amount=price,
    currency='gbp',
    customer=customer_id,
    automatic_payment_methods={
      'enabled': True,
    },
    )

    return {
        'statusCode': 200,
        'body': json.dumps({
            'paymentIntent': paymentIntent.client_secret,
            'ephemeralKey': ephemeralKey.secret,
            'customer': customer_id,
            'publishableKey': 'pk_test_51NJwFSDXdklEKm0R8JRHkohXh2qEKG57G837zZCKOUFXlyjTNkHa2XOSUa0zhN2rQaVkd9NPTykrdC9IRnoBlZ7Z00uMUWz549'
        })
    }
