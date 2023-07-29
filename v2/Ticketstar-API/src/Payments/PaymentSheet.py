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
        if price < 20:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'message': 'Invalid price',
                })
            }
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

        application_fee = round(calculate_application_fee(price))

        payment_intent = stripe.PaymentIntent.create(
            amount=price,
            currency='gbp',
            customer=stripe_id,
            automatic_payment_methods={
                'enabled': True,
            },
            application_fee_amount=application_fee,
            transfer_data={'destination': seller_stripe_id}
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


def calculate_application_fee(price):
    # takes the price in pennies
    from GetFees import get_fees
    fees = get_fees()

    stripe_fixed_fee = fees['stripe_fixed_fee'] # pennies
    stripe_variable_fee = fees['stripe_variable_fee'] # percentage as decimal

    platform_fixed_fee = fees['platform_fixed_fee'] # pennies
    platform_variable_fee = fees['platform_variable_fee'] # percentage as decimal

    p_goal = (price * (1 - stripe_variable_fee)) - stripe_fixed_fee

    stripe_fee = round(price - p_goal, 2)

    platform_fee = round(price * platform_variable_fee, 2) + platform_fixed_fee

    return stripe_fee + platform_fee
