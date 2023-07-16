
"""

Used for the search features, for events

Search url: https://api.fixr.co/search/events?query=timep

location query for Exeter: &lat=50.72604&lon=-3.52749

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

    response = requests.get(url)

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


def get_event_info(event_id):
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

            ticket_asks = get_asks_by_fixr_ids(event_id, ticket_id)

        except DatabaseException:

            ticket_asks = None

        ticket_info['asks'] = ticket_asks

        tickets.append(ticket_info)

    tickets = sorted(tickets, key=lambda d: d['id'])

    event_parameters_to_pull = ['id', 'name', 'open_time', 'close_time', 'sold_out', 'venue']

    event = {}

    for parameter in event_parameters_to_pull:
        event[parameter] = data[parameter]

    event['tickets'] = tickets

    return event