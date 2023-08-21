import json
import logging
from DatabaseActions import get_customer, create_customer
from DatabaseActions import get_ask, get_seller
from DatabaseConnector import Database
import stripe as stripe

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):

    secret_key = "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"
    publishable_key = "pk_live_51NJwFSDXdklEKm0RH9UR7RgQ2kPsEQvbFaSJKVl5PnBMNWVIVT88W4wMIo8IIm9A6TvKOBOVV4xPSN9tvPMHAZOJ00uA9XSbKi"

    secret_key = "sk_test_51NJwFSDXdklEKm0RDJhFhwEBcJLEPOtBtdeovg18JHIIu4HxkXLge19WAPvUap3V0drBuJOgrvccYNgCFaLfsW3x00ME3KwKgi"
    publishable_key = "pk_test_51NJwFSDXdklEKm0R8JRHkohXh2qEKG57G837zZCKOUFXlyjTNkHa2XOSUa0zhN2rQaVkd9NPTykrdC9IRnoBlZ7Z00uMUWz549"

    try:
        body = json.loads(event['body'])

        price = int(float(body['price']) * 100)
        if price < 100:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'message': 'Invalid price',
                })
            }
        user_email = body['user_email']
        user_id = body['user_id']
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
        with Database() as database:

            results = get_customer(database, user_id)

            seller_id = get_ask(database, ask_id)['seller_user_id']

            seller_stripe_id = get_seller(database, seller_id)[0][0]

            stripe.api_key = secret_key

            if len(results) == 0 or results[0][0] is None:
                new_customer = stripe.Customer.create(
                    name=user_name,
                    email=user_email,
                )

                stripe_id = new_customer['id']

                create_customer(database, user_id, stripe_id)
            else:
                stripe_id = results[0][0]

            ephemeral_key = stripe.EphemeralKey.create(
                customer=stripe_id,
                stripe_version='2022-11-15',
            )

            application_fee = round(calculate_application_fee(price, ask_id))

            payment_intent = get_payment_intent(database, ask_id, user_id, price)

            logger.info('payment_intent: ' + str(payment_intent))

            if payment_intent is None:

                logger.info('creating payment intent')

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

                insert_payment_intent(database, ask_id, payment_intent.id, price)

            return {
                'statusCode': 200,
                'body': json.dumps({
                    'paymentIntent': payment_intent.client_secret,
                    'ephemeralKey': ephemeral_key.secret,
                    'customer': stripe_id,
                    'publishableKey': publishable_key
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


def calculate_application_fee(price, ask_id):
    # takes the price in pennies
    from GetFees import get_fees_by_ask_id
    fees = get_fees_by_ask_id(ask_id)

    stripe_fixed_fee = fees['stripe_fixed_fee'] # pennies
    stripe_variable_fee = fees['stripe_variable_fee'] # percentage as decimal

    platform_fixed_fee = fees['platform_fixed_fee'] # pennies
    platform_variable_fee = fees['platform_variable_fee'] # percentage as decimal

    p_goal = (price * (1 - stripe_variable_fee)) - stripe_fixed_fee

    stripe_fee = round(price - p_goal, 2)

    platform_fee = round(price * platform_variable_fee, 2) + platform_fixed_fee

    return stripe_fee + platform_fee


def insert_payment_intent(database, ask_id, payment_intent_id, price):
    sql = "UPDATE asks SET payment_intent=%s, payment_intent_price=%s WHERE ask_id=%s"
    database.execute_update_query(sql, (payment_intent_id, price, ask_id))


def get_payment_intent(database, ask_id, user_id, price):
    sql = "SELECT payment_intent, buyer_user_id, payment_intent_price FROM asks WHERE ask_id=%s"

    results = database.execute_select_query(sql, (ask_id, ))
    if len(results) == 0:
        return None
    else:
        result = results[0]
        payment_intent = result[0]
        buyer_user_id = result[1]
        payment_intent_price = result[2]

        if buyer_user_id == user_id and payment_intent is not None:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent)
            customer_id = payment_intent.customer

            get_customer_id_sql = "SELECT user_id FROM stripe WHERE customer_id=%s"

            results = database.execute_select_query(get_customer_id_sql, (customer_id, ))

            if len(results) == 0:
                return None
            else:
                _payment_intent_user_id = results[0][0]
                if _payment_intent_user_id == user_id:
                    if price == payment_intent_price:
                        return payment_intent

    return None
