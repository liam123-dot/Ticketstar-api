# """
#
# Function to fulfill an ask once payment has been confirmed
# add some confirmation about making sure the reserver and buyer are the same
#
# """
import json
import logging
import time

import stripe

from DatabaseConnector import Database

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):

    try:

        body = json.loads(event['body'])

        payment_intent_id = body['data']['object']['id']

    except Exception as e:

        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Invalid body ' + str(e)
            })
        }

    try:

        with Database() as database:
            current_time = time.time()
            sql = 'UPDATE asks SET fulfilled=1, purchase_time=%s WHERE payment_intent=%s'

            database.execute_update_query(sql, (current_time, payment_intent_id))
            send_listing_sold_email(database, payment_intent_id)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Success'
            })
        }

    except Exception as e:
        issue_refund(payment_intent_id)
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Listing not fulfilled and refund processed'
            })
        }


def issue_refund(payment_intent_id):
    stripe.api_key = 'sk_test_51NJwFSDXdklEKm0RDJhFhwEBcJLEPOtBtdeovg18JHIIu4HxkXLge19WAPvUap3V0drBuJOgrvccYNgCFaLfsW3x00ME3KwKgi'

    stripe.Refund.create(
        payment_intent=payment_intent_id,
        refund_application_fee=True,
        reverse_transfer=True
    )


def send_listing_sold_email(database, payment_intent):

    sql = "SELECT seller_user_id, price, ticket_id FROM asks WHERE payment_intent=%s"

    results = database.execute_select_query(sql, (payment_intent, ))[0]

    seller_user_id = results[0]
    price = results[1]
    ticket_id = results[2]

    user_email = get_user_email(seller_user_id)
    send_email(user_email, price, get_ticket_info(database, ticket_id))


def get_user_email(user_id):
    import boto3
    cognito = boto3.client('cognito-idp')

    from GetCognitoCreds import get_secret
    cognito_creds = get_secret()

    USER_POOL_ID = cognito_creds['USER_POOL_ID']

    response = cognito.list_users(
        UserPoolId=USER_POOL_ID,
        AttributesToGet=[
            'email',
        ],
        Filter='username=\"' + user_id + '\"'
    )

    email = response['Users'][0]['Attributes'][0]['Value']
    return email


def get_ticket_info(database, ticket_id):
    sql = "SELECT ticket_name, event_name FROM tickets WHERE ticket_id=%s"

    result = database.execute_select_query(sql, ticket_id)[0]

    return {
        'ticket_name': result[0],
        'event_name': result[1]
    }


def send_email(user_email, price, ticket_info):
    import boto3
    ses = boto3.client('ses')

    response = ses.send_email(
        Source='congratulations@ticketstar.uk',
        Destination={
            'ToAddresses': [
                user_email
            ]
        },
        Message={
            'Subject': {
                'Data': '✅You sold your ticket!'
            },
            'Body': {
                'Html': {
                    'Data': f"""
                        <html>
                        <head></head>
                        <body>
                            <p>TICKET: {ticket_info['ticket_name']}</p>
                            <p>EVENT: {ticket_info['event_name']}</p>
                            <p>PAYOUT: £{"{:.2f}".format(price)}</p>
                            <p>Click <a href='https://dashboard.stripe.com/dashboard'>here</a> to check your Stripe account for payout information.</p>
                        </body>
                        </html>
                        """
                }
            }
        }
    )
