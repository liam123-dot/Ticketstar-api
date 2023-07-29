
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

        query_string_parameters = event['queryStringParameters']
        filter_ = query_string_parameters['filter']

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

        info = get_purchase_info(user_id, filter_)

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

def get_purchase_info(buyer_user_id, filter_):
    from DatabaseActions import get_purchases, get_ticket_info, get_fixr_account_details_from_real_ticket_id, get_ticket_reference_by_real_ticket_id, mark_ask_as_claimed, remove_relationship, get_fixr_account_details_from_account_id
    from FixrAccount import FixrAccount

    purchases = get_purchases(buyer_user_id)

    response = {}

    for purchase in purchases:
        ask_id = purchase[0]
        price = purchase[1]
        ticket_id = purchase[2]
        claimed = purchase[3] == b'\x01'
        real_ticket_id = purchase[4]

        ticket_info = get_ticket_info(ticket_id)[0]

        ticket_name = ticket_info[0]
        event_name = ticket_info[1]
        open_time = ticket_info[2]
        close_time = ticket_info[3]
        image_url = ticket_info[4]
        fixr_event_id = ticket_info[5]
        fixr_ticket_id = ticket_info[6]

        if filter_ == 'past' and close_time > time.time():
            continue
        elif filter_ == 'upcoming' and close_time < time.time():
            continue

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
            account_id, account_details = get_fixr_account_details_from_real_ticket_id(real_ticket_id)

            account_details = account_details[0]
            fixr_username = account_details[0]
            fixr_password = account_details[1]
            ticket_reference = get_ticket_reference_by_real_ticket_id(real_ticket_id)

            with requests.session() as s:

                account = FixrAccount(s, fixr_username, fixr_password)

                ticket_owned = account.check_ownership(ticket_reference)

                if not ticket_owned:
                    mark_ask_as_claimed(ask_id)
                    remove_relationship(account_id, ticket_id)
                    claimed = True

        response[fixr_event_id]['tickets'][fixr_ticket_id]['purchases'].append({
            'ask_id': ask_id,
            'price': price,
            'claimed': claimed
        })

    if filter_ == 'unclaimed':
        response = filter_out_claimed(response)

    return response


def filter_out_claimed(data):
    events_to_remove = []

    for event in data.keys():
        tickets_to_remove = []

        for ticket in data[event]['tickets'].keys():
            purchases_to_remove = []

            for purchase in data[event]['tickets'][ticket]['purchases']:
                if purchase['claimed']:
                    purchases_to_remove.append(purchase)

            for purchase in purchases_to_remove:
                data[event]['tickets'][ticket]['purchases'].remove(purchase)

            if len(data[event]['tickets'][ticket]['purchases']) == 0:
                tickets_to_remove.append(ticket)

        for ticket in tickets_to_remove:
            data[event]['tickets'].pop(ticket)

        if len(data[event]['tickets']) == 0:
            events_to_remove.append(event)

    for event in events_to_remove:
        data.pop(event)

    return data
