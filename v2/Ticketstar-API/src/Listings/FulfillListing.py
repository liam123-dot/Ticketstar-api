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

