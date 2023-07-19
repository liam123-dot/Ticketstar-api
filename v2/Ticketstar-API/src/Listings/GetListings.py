

"""

Function to get all the listings with a certain requirement

Can be used to get purchases/listings

"""
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):

    try:
        headers = event['headers']
        user_id = headers['Authorization']
        query_string = event['queryStringParameters']
        option = query_string['option'].lower()
        if 'filter' in query_string.keys():
            filter_option = query_string['filter']
        else:
            filter_option = None
        if option not in ['purchases', 'listings']:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'message': 'Invalid option'
                })
            }
    except KeyError as e:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Invalid requests parameters: ' + str(e)
            })
        }

    try:

        if option == 'purchases':
            info = get_purchase_info(user_id)
        else:
            info = get_listing_info(user_id, filter_option)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'info': info
            })
        }

    except Exception as e:
        logger.error("error getting listing/purchase error: %s", e)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'internal server error'
            })
        }


def get_purchase_info(buyer_user_id):
    from DatabaseActions import get_purchases, get_ticket_info

    purchases = get_purchases(buyer_user_id)

    response = {}

    loaded_tickets = []

    for purchase in purchases:
        ask_id = purchase[0]
        price = purchase[1]
        ticket_id = purchase[2]

        if ticket_id not in loaded_tickets:
            loaded_tickets.append(ticket_id)
            ticket_info = get_ticket_info(ticket_id)[0]

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

        response[fixr_event_id]['tickets'][fixr_ticket_id]['purchases'].append({
            'ask_id': ask_id,
            'price': price
        })

    return response


def get_listing_info(seller_user_id, filter_option=None):
    from DatabaseActions import get_listings, get_ticket_info

    listings = get_listings(seller_user_id)

    response = {}

    loaded_tickets = []

    for listing in listings:
        ask_id = listing[0]
        price = listing[1]
        ticket_id = listing[2]
        fulfilled = listing[3] == b'\x01'
        listed = listing[4] == b'\x01'

        if filter_option is not None:
            if filter_option == 'sold' and not fulfilled:
                continue
            elif filter_option == 'unsold' and fulfilled:
                continue

        if ticket_id not in loaded_tickets:
            loaded_tickets.append(ticket_id)
            ticket_info = get_ticket_info(ticket_id)[0]

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

        response[fixr_event_id]['tickets'][fixr_ticket_id]['listings'].append({
            'ask_id': ask_id,
            'price': price,
            'fulfilled': fulfilled,
            'listed': listed
        })

    return response
