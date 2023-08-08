
import json
import logging
import time

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
        logger.error("Exception get_purchases, error: %s", str(e))
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Internal Server Error'
            })
        }

    try:

        info = get_purchase_info(user_id)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'info': info
            })
        }

    except Exception as e:
        logger.error("error getting purchase error: %s", str(e))
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'internal server error'
            })
        }

def get_purchase_info(buyer_user_id):
    from DatabaseConnector import Database
    from DatabaseActions import get_purchases, get_ticket_info, get_fixr_account_details_from_real_ticket_id, get_ticket_reference_by_real_ticket_id, mark_ask_as_claimed, remove_relationship
    from FixrAccount import FixrAccount

    with Database() as database:
        purchases = get_purchases(database, buyer_user_id)

        response = {}

        for purchase in purchases:
            ask_id = purchase[0]
            price = purchase[1]
            ticket_id = purchase[2]
            claimed = purchase[3] == b'\x01'
            real_ticket_id = purchase[4]

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
                    'purchases': []
                }

            if not claimed:
                account_id, account_details = get_fixr_account_details_from_real_ticket_id(database, real_ticket_id)

                account_details = account_details[0]
                fixr_username = account_details[0]
                fixr_password = account_details[1]
                ticket_reference = get_ticket_reference_by_real_ticket_id(database, real_ticket_id)

                with requests.session() as s:

                    account = FixrAccount(s, fixr_username, fixr_password)

                    ticket_owned = account.check_ownership(ticket_reference)

                    if not ticket_owned:
                        mark_ask_as_claimed(database, ask_id)
                        remove_relationship(database, account_id, ticket_id)
                        claimed = True

            response[fixr_event_id]['tickets'][fixr_ticket_id]['purchases'].append({
                'ask_id': ask_id,
                'price': price,
                'claimed': claimed
            })

        return response
