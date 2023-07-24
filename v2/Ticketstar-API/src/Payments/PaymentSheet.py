import json
import logging
from DatabaseActions import get_customer, create_customer
from DatabaseActions import get_ask, get_seller
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
        ask_id = body['ask_id']

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

        seller_id = get_ask(ask_id)['seller_user_id']

        seller_stripe_id = get_seller(seller_id)[0][0]

        stripe.api_key = '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'

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
        print(seller_stripe_id)
        payment_intent = stripe.PaymentIntent.create(
            amount=price,
            currency='gbp',
            customer=stripe_id,
            automatic_payment_methods={
                'enabled': True,
            },
            application_fee_amount=10,
            transfer_data={'destination': seller_stripe_id}
        )

        print(payment_intent)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'paymentIntent': payment_intent.client_secret,
                'ephemeralKey': ephemeral_key.secret,
                'customer': stripe_id,
                'publishableKey': 'pk_live_51NJwFSDXdklEKm0RH9UR7RgQ2kPsEQvbFaSJKVl5PnBMNWVIVT88W4wMIo8IIm9A6TvKOBOVV4xPSN9tvPMHAZOJ00uA9XSbKi'
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
