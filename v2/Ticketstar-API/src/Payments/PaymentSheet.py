import json
import logging
from DatabaseActions import get_customer, create_customer
import stripe as stripe

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):

    try:
        body = json.loads(event['body'])

        price = int(float(body['price']) * 100)
        user_email = body['user_email']
        user_id = body['user_id']
        user_phone_number = body['user_phone_number']
        user_name = body['user_name']

    except KeyError as e:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Invalid requests parameters: ' + str(e)
            })
        }
    except Exception as e:
        logger.error("Exception get_purchases, error: %s", str(e))
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Internal Server Error'
            })
        }

    try:

        results = get_customer(user_id)

        stripe.api_key = 'sk_test_51NJwFSDXdklEKm0RDJhFhwEBcJLEPOtBtdeovg18JHIIu4HxkXLge19WAPvUap3V0drBuJOgrvccYNgCFaLfsW3x00ME3KwKgi'

        if len(results) == 0:
            new_customer = stripe.Customer.create(
                name=user_name,
                email=user_email,
                phone=user_phone_number,
            )

            stripe_id = new_customer['id']

            create_customer(user_id, stripe_id)
        else:
            stripe_id = results[0][0]

        ephemeral_key = stripe.EphemeralKey.create(
            customer=stripe_id,
            stripe_version='2022-11-15',
        )
        payment_intent = stripe.PaymentIntent.create(
            amount=price,
            currency='gbp',
            customer=stripe_id,
            automatic_payment_methods={
                'enabled': True,
            },
        )

        return {
            'statusCode': 200,
            'body': json.dumps({
                'paymentIntent': payment_intent.client_secret,
                'ephemeralKey': ephemeral_key.secret,
                'customer': stripe_id,
                'publishableKey': 'pk_test_51NJwFSDXdklEKm0R8JRHkohXh2qEKG57G837zZCKOUFXlyjTNkHa2XOSUa0zhN2rQaVkd9NPTykrdC9IRnoBlZ7Z00uMUWz549'
            })
        }

    except Exception as e:
        logger.error("ERROR payment sheet, error: %s", e)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Server Error'
            })
        }
