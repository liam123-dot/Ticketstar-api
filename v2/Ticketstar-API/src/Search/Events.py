
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


