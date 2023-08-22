
"""

Function to get all the listings with a certain requirement

Can be used to get purchases/listings

if listed=0, needs a link for transfer url, not too difficult.

"""
import json
import logging

import requests

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):

    try:
        headers = event['headers']
        user_id = headers['Authorization']

    except KeyError as e:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Invalid requests parameters: ' + str(e)
            })
        }
    except Exception as e:
        logger.error("Error loading parameters: %s", str(e))

        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Invalid parameters'
            })
        }

    try:

        info = get_listing_info(user_id)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'info': info
            })
        }

    except Exception as e:
        logger.error("error getting listing error: %s", e)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'internal server error'
            })
        }

def get_listing_info(seller_user_id, filter_option=None):
    from DatabaseActions import get_listings, get_ticket_info, get_ticket_ownership, get_fixr_account_details_from_account_id, update_ticket_ownership, remove_relationship
    from DatabaseConnector import Database

    with Database() as database:

        listings = get_listings(database, seller_user_id)

        response = {}

        for listing in listings:
            ask_id = listing[0]
            price = listing[1]
            ticket_id = listing[2]
            fulfilled = listing[3] == b'\x01'
            listed = listing[4] == b'\x01'
            real_ticket_id = listing[5]

            if filter_option is not None:
                if filter_option == 'sold' and not fulfilled:
                    continue
                elif filter_option == 'unsold' and fulfilled:
                    continue

            ticket_info = get_ticket_info(database, ticket_id)[0]

            ticket_name = ticket_info[0]
            event_name = ticket_info[1]
            open_time = ticket_info[2]
            close_time = ticket_info[3]
            image_url = ticket_info[4]
            fixr_event_id = ticket_info[5]
            fixr_ticket_id = ticket_info[6]

            if fixr_event_id not in response.keys():
                response[fixr_event_id] = {
                    'event_name': event_name,
                    'open_time': open_time,
                    'close_time': close_time,
                    'image_url': image_url,
                    'tickets': {}
                }

            if fixr_ticket_id not in response[fixr_event_id]['tickets']:
                response[fixr_event_id]['tickets'][fixr_ticket_id] = {
                    'ticket_name': ticket_name,
                    'listings': []
                }

            if not listed:
                results = get_ticket_ownership(database, real_ticket_id)
                ownership = results[0] == b'\x01'
                account_id = results[1]
                ticket_reference = results[2]

                if ownership:
                    account_details = get_fixr_account_details_from_account_id(database, account_id)[0]
                    fixr_username = account_details[0]
                    fixr_password = account_details[1]

                    from FixrAccount import FixrAccount
                    with requests.session() as s:
                        account = FixrAccount(s, fixr_username, fixr_password)

                    ticket = account.check_ownership(ticket_reference)
                    if not ticket:
                        update_ticket_ownership(real_ticket_id, False)
                        remove_relationship(database, account_id, ticket_id)

            else:
                ownership = None

            response[fixr_event_id]['tickets'][fixr_ticket_id]['listings'].append({
                'ask_id': ask_id,
                'price': price,
                'fulfilled': fulfilled,
                'listed': listed,
                'ownership': ownership
            })

        return response
