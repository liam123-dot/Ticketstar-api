"""

lambda function that is called when a user is prompted to create a stripe account before they can sell tickets

requires: they're phone number, email, first and last name, user_id

the account_id should be stored in the stripe database so that funds can be routed.
need to add functionality to check the account is fully set up before funds are routed.

"""
import json
import time

import stripe
from DatabaseConnector import Database
from CheckConnectedAccount import check_stripe_account_enabled
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):

    try:
        body = json.loads(event['body'])
        user_id = body['user_id']
        first_name = body['first_name']
        last_name = body['last_name']
        phone_number = body['phone_number']
        email = body['email']
    except KeyError as e:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Invalid parameters, ' + str(e)
            })
        }
    except json.JSONDecoder as e:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Invalid body sent, ' + str(e)
            })
        }

    try:

        with Database() as database:
            # query to check if the user already has a stripe seller account
            sql = "SELECT seller_id FROM stripe WHERE user_id=%s and seller_id is not NULL"
            results = database.execute_select_query(sql, (user_id, ))
            if len(results) == 0:
                logger.info("Creating account for user: " + str(user_id))
                account = create_stripe_account(first_name, last_name, email, phone_number)

                account_id = account['id']

                # query to add seller_id to stripe database
                sql = """INSERT INTO stripe(user_id, seller_id) VALUES(%s, %s)
                 ON DUPLICATE KEY UPDATE seller_id = VALUES(seller_id)"""

                database.execute_update_query(sql, (user_id, account_id))

                url = generate_account_link(account_id, user_id)

                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'link': url
                    })
                }

            else:
                seller_id = results[0][0]
                further_action_required = check_stripe_account_enabled(seller_id)

                if not further_action_required:
                    return {
                        'statusCode': 200,
                        'body': json.dumps({
                            'link': None
                        })
                    }
                else:
                    account_link = generate_account_link(seller_id, user_id)

                    return {
                        'statusCode': 200,
                        'body': json.dumps({
                            'link': account_link
                        })
                    }
    except Exception as e:
        logger.error("Error creating account: %s", str(e))
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Server error'
            })
        }


def generate_account_link(account_id, user_id):
    stripe.api_key = "sk_test_51NJwFSDXdklEKm0RDJhFhwEBcJLEPOtBtdeovg18JHIIu4HxkXLge19WAPvUap3V0drBuJOgrvccYNgCFaLfsW3x00ME3KwKgi"

    logger.info("Creating account onboarding link for user: " + str(user_id))

    account_link = stripe.AccountLink.create(
        account=account_id,
        refresh_url="https://example.com/reauth",
        return_url="https://example.com/return",
        type="account_onboarding",
    )

    return account_link['url']


def create_stripe_account(first_name, last_name, email, phone_number):
    stripe.api_key = "sk_test_51NJwFSDXdklEKm0RDJhFhwEBcJLEPOtBtdeovg18JHIIu4HxkXLge19WAPvUap3V0drBuJOgrvccYNgCFaLfsW3x00ME3KwKgi"

    account = stripe.Account.create(
        type='standard',
        email=email,
        country='GB',
        business_type='individual',
        individual={
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
        },
        business_profile={
            "mcc": "7922",
            "name": "Ticketstar",
            "product_description": "Fixr Tickets",
            "support_address": None,
            "support_email": None,
            "support_phone": phone_number,
            "support_url": None,
            "url": "www.ticketstar.uk"
        },
    )

    return account
