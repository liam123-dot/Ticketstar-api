
"""

Used for the search features, for events

Search url: https://api.fixr.co/search/events?query=timep

location query for Exeter: &lat=50.72604&lon=-3.52749

get event needs to show exactly how the screen should look so that there isn't any processing required on user side
and to allow for easy changes in future

should take the id of the user is searching and return each ticket as an option:

each tickets object should already have assessed what that user should display:

{

    name:
    ticket_id:
    fixr_price:
    listing: { # just show the cheapest to purchase,
        ask_id,
        cheapest,
        ask_price,
        seller_id
    }


}

"""
import json
import random
import time
from DatabaseActions import check_event_has_tickets

from FixrExceptions import FixrApiException

import requests
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def search(search_query, user_id, limit=None, offset=None):
    if limit is None:
        limit = 4
    if offset is None:
        offset = 0
    url = f"https://api.fixr.co/search/events?query={search_query}&limit={limit}&offset={offset}"

    from datetime import datetime

    def to_epoch(time_string):
        dt_object = datetime.strptime(time_string, '%Y-%m-%dT%H:%M:%SZ')
        return int(dt_object.timestamp())

    headers = {
        "Accept": "application/json; version=3.0"
    }

    response = requests.get(url, headers=headers)

    if not response.ok:
        logger.error("Response error from fixr. Response code: %s, Response text: %s", response.status_code, response.text)

        raise FixrApiException("Invalid response from fixr api")

    data = response.json()

    events = []

    from DatabaseConnector import Database

    try:

        with Database() as database:

            for event in data['results']:
                events.append({
                    'fixr_id': event['id'],
                    'name': event['name'],
                    'image_url': event['image_url'],
                    'open_time': to_epoch(event['opens_at']),
                    'close_time': to_epoch(event['closes_at']),
                    'venue': event['venue']['name'] if event.get('venue') else 'No venue attached',
                    # will be used to verify whether tickets are available. i.e. null if not
                    'has_listings': check_event_has_tickets(database, event['id'], user_id)
                })

        events = sorted(events, key=lambda d: d['open_time'])

    except KeyError as e:
        logger.error("Error parsing events, error: %s, data: %s", e, data)
        raise FixrApiException("Invalid response from fixr")

    return events


def get_event_info(event_id, user_id):
    from DatabaseConnector import Database
    from DatabaseActions import get_asks_by_ticket_id, get_event_tickets, create_ticket_id

    with Database() as database:

        event_info = get_event_tickets(database, event_id)

        if len(event_info) == 0:
            event_url = "https://api.fixr.co/api/v2/app/event/" + str(event_id) + "?"

            response = requests.get(event_url)

            if not response.ok:
                logger.error("Response error from fixr. Response code: %s, Response text: %s", response.status_code,
                             response.text)

                raise FixrApiException("Bad fixr response")

            try:

                data = response.json()

            except Exception as e:
                raise FixrApiException(e)

            event_parameters_to_pull = ['id', 'name', 'open_time', 'close_time', 'venue', 'image_url']

            event = {}

            for event_parameter in event_parameters_to_pull:
                try:
                    if event_parameter == 'id':
                        event['fixr_event_id'] = data['id']
                    elif event_parameter == 'image_url':
                        event['image_url'] = data['event_image']
                    else:
                        event[event_parameter] = data[event_parameter]
                except KeyError as e:
                    logger.error("Error with event parameter: %s. Error given: %s, ticket data: %s", event_parameter, e, data)

            ticket_parameters_to_pull = ['id', 'name', 'price', 'booking_fee', 'promo_code_required', 'entry_count',
                                         'max_per_user', 'sold_out', 'last_entry']
            tickets = []

            for ticket in data['tickets']:
                ticket_info = {}

                for parameter in ticket_parameters_to_pull:
                    try:

                        if parameter == 'id':
                            ticket_info['fixr_ticket_id'] = ticket['id']
                        else:
                            ticket_info[parameter] = ticket[parameter]

                    except KeyError as e:
                        logger.error("Error with ticket parameter: %s. Error given: %s, ticket data: %s", parameter, e, ticket)

                ticket_id = create_ticket_id(database, event, ticket_info)
                ticket_info['id'] = ticket_id
                ticket_info['listing'] = None

                tickets.append(ticket_info)

            tickets = sorted(tickets, key=lambda d: d['id'])

            event['tickets'] = tickets

            return event

        else:

            event = {}

            event_attribute_indexes = {
                'fixr_event_id': 0,
                'event_name': 1,
                'open_time': 2,
                'close_time': 3,
                'venue_name': 4,
                'image_url': 5,
            }

            ticket_attribute_indexes = {
                'fixr_ticket_id': 6,
                'ticket_id': 7,
                'ticket_name': 8,
                'price': 9,
                'booking_fee': 10,
                'promo_code_required': 11,
                'entry_count': 12,
                'max_per_user': 13,
                'sold_out': 14,
                'last_entry': 15
            }

            tickets = []

            total_tickets = 0

            for i in range(0, len(event_info)):
                data = event_info[i]
                if i == 0:
                    for key in event_attribute_indexes.keys():
                        index = event_attribute_indexes[key]
                        event[key] = data[index]
                ticket = {}
                for key in ticket_attribute_indexes.keys():
                    index = ticket_attribute_indexes[key]
                    if key == 'ticket_id':
                        ticket['id'] = data[index]
                    else:
                        ticket[key] = data[index]

                ticket_asks = get_asks_by_ticket_id(ticket['id'], database)

                ticket['listing'] = filter_ticket_asks(ticket_asks, user_id)
                ticket['name'] = ticket['ticket_name']

                listing_count = ticket_asks['ask_count']
                ticket['listing_count'] = listing_count
                total_tickets += listing_count

                tickets.append(ticket)

            from CalculateSearchCount import calculate_event_searches
            current_time = time.time()
            event['search_count'] = calculate_event_searches(database, event_id, current_time - 3600, current_time)

            tickets = sorted(tickets, key=lambda d: d['id'])

            event['tickets'] = tickets
            event['total_tickets'] = total_tickets
            return event


def filter_ticket_asks(asks, user_id):
    import time
    """
    { # just show the cheapest to purchase,
        ask_id,
        cheapest,
        ask_price,
    }


    """

    ask_count = asks['ask_count']
    asks = asks['asks']

    if ask_count == 0:
        return None

    index = 0
    cheapest_ticket = {}

    while True:
        ticket = asks[index]

        if ticket['reserved']:
            current_time = round(time.time())
            if ticket['reserve_timeout'] < current_time:
                ticket['reserved'] = False
                cheapest_ticket = {
                    'ask_id': ticket['ask_id'],
                    'ask_price': ticket['price'],
                    'purchasable': ticket['seller_user_id'] != user_id
                }
            elif ticket['buyer_user_id'] == user_id:
                cheapest_ticket = {
                    'ask_id': ticket['ask_id'],
                    'ask_price': ticket['price'],
                    'purchasable': True
                }
                break

        elif user_id != ticket['seller_user_id'] and not ticket['reserved']:
            cheapest_ticket = {
                'ask_id': ticket['ask_id'],
                'ask_price': ticket['price'],
                'purchasable': ticket['seller_user_id'] != user_id
            }
            break

        elif user_id == ticket['seller_user_id'] and not ticket['reserved']:
            cheapest_ticket = {
                'ask_id': ticket['ask_id'],
                'ask_price': ticket['price'],
                'purchasable': False
            }
            break

        index += 1

        if index == ask_count:
            break

    if len(cheapest_ticket) == 0:
        return None
    else:
        return cheapest_ticket

