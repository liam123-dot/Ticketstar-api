
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

from FixrExceptions import FixrApiException

import requests
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def search(search_query, limit=None, offset=None):
    if limit is None:
        limit = 6
    if offset is None:
        offset = 0
    url = f"https://api.fixr.co/search/events?query={search_query}&limit={limit}&offset={offset}"

    headers = {
        "Accept": "application/json; version=3.0"
    }

    response = requests.get(url, headers=headers)

    if not response.ok:
        logger.error("Response error from fixr. Response code: %s, Response text: %s", response.status_code, response.text)

        raise FixrApiException("Invalid response from fixr api")

    data = response.json()

    events = []

    try:

        for event in data['results']:
            events.append({
                'fixr_id': event['id'],
                'name': event['name'],
                'image_url': event['image_url'],
                'open_time': event['opens_at'],
                'close_time': event['closes_at'],
                'venue': event['venue']['name'] if event.get('venue') else 'No venue attached',
                'cheapest_ticket': event['cheapest_ticket'],
                # will be used to verify whether tickets are available. i.e. null if not
                'sold_out': event['is_sold_out']
            })

    except KeyError as e:
        logger.error("Error parsing events, error: %s, data: %s", e, data)
        raise FixrApiException("Invalid response from fixr")

    return events


def get_event_info(event_id, user_id):
    from DatabaseActions import get_asks_by_fixr_ids
    from DatabaseException import DatabaseException

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

    event_id = data['id']

    ticket_parameters_to_pull = ['id', 'name', 'price', 'booking_fee', 'promo_code_required', 'entry_count', 'currency',
                                 'max_per_user', 'sold_out', 'not_yet_valid', 'expired', 'last_entry']

    tickets = []

    for ticket in data['tickets']:
        ticket_id = ticket['id']

        ticket_info = {}

        for parameter in ticket_parameters_to_pull:
            try:
                ticket_info[parameter] = ticket[parameter]
            except KeyError as e:
                logger.error("Error with parameter: %s. Error given: %s, ticket data: %s", parameter, e, ticket)

        try:

            ticket_id, ticket_asks = get_asks_by_fixr_ids(event_id, ticket_id)

        except DatabaseException:

            ticket_asks = None

        ticket_info['fixr_id'] = ticket_info['id']
        ticket_info['id'] = ticket_id

        ticket_info['listing'] = filter_ticket_asks(ticket_asks, user_id)

        logger.info(ticket_info)

        tickets.append(ticket_info)

    tickets = sorted(tickets, key=lambda d: d['id'])

    event_parameters_to_pull = ['id', 'name', 'open_time', 'close_time', 'sold_out', 'venue']

    event = {}

    for parameter in event_parameters_to_pull:
        event[parameter] = data[parameter]

    event['tickets'] = tickets

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
            elif ticket['buyer_user_id'] == user_id:
                cheapest_ticket = {
                    'ask_id': ticket['ask_id'],
                    'cheapest': index == 0,
                    'ask_price': ticket['price'],
                }
                break

        if ticket['seller_user_id'] != user_id and not ticket['reserved']:
            cheapest_ticket = {
                'ask_id': ticket['ask_id'],
                'cheapest': index == 0,
                'ask_price': ticket['price'],
            }
            break

        index += 1

        if index == ask_count:
            break

    if len(cheapest_ticket) == 0:
        return None
    else:
        return cheapest_ticket
