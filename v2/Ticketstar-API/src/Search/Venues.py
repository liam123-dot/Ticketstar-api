"""

The functions here will serve the same function as the organisers

using the url

venues_url = f"https://api.fixr.co/search/venues?query={query}&limit=6&offset=0&popularity__boost=0"

Each venue gets a response like the following:
{
    "id": 1422,
    "name": "Timepiece ",
    "city": "Exeter",
    "image_url": "https://fixr-cdn.fixr.co/images/venue/logo/a37e863f02604ec09c11743f55c880c6.jpg",
    "routing_part": "1422"
},

we use the url:

"https://api.fixr.co/api/v2/app/venue/{event_id}?"

to fetch the events associated with that venue as well as being used just to quickly checl
if the venue has any active events when deciding whether to show it.

"""

from FixrExceptions import FixrApiException
import requests
import logging
import json
import concurrent.futures

logger = logging.getLogger()
logger.setLevel(logging.INFO)

headers = {
    "Accept": "application/json; version=3.0"
}


def check_venue_has_events(venue_id):

    return len(get_venue_events(venue_id))


def get_venue_events(venue_id):
    url = f"https://api.fixr.co/api/v2/app/venue/{venue_id}?"

    response = requests.get(url)

    if not response.ok:
        logger.error("Response error from fixr get_venue_events. Response code: %s, Response text: %s", response.status_code,
                     response.text)

        raise FixrApiException("Invalid response from fixr api")

    try:
        data = response.json()
    except json.JSONDecodeError:
        logger.error("Error decoding venue response into json, get_venue_events, response: %s",
                     response.content)
        raise FixrApiException("Json decode error")

    events = data['events']

    return events


def search(query, limit=None, offset=None):
    if limit is None:
        limit = 6
    if offset is None:
        offset = 0
    venues_url = f"https://api.fixr.co/search/venues?query={query}&limit={limit}&offset={offset}&popularity__boost=0"

    response = requests.get(venues_url, headers=headers)

    if not response.ok:
        logger.error("Response error from fixr. Response code: %s, Response text: %s", response.status_code,
                     response.text)

        raise FixrApiException("Invalid response from fixr api")

    try:
        data = response.json()
    except json.JSONDecodeError:
        logger.error("Error decoding venue response into json, response: %s", response.content)
        raise FixrApiException("Json decode error")

    venues = []

    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_venue = {executor.submit(check_venue_has_events, venue['id']): venue for
                                   venue in data['results']}

            for future in concurrent.futures.as_completed(future_to_venue):
                venue = future_to_venue[future]
                venue_has_events = future.result()

                if venue_has_events:
                    venues.append({
                        'fixr_id': venue['id'],
                        'name': venue['name'],
                        'image_url': venue['image_url'],
                        'city': venue['city'],
                        'slug': None
                        })

                if len(venues) == 3:
                    break

        return venues

    except FixrApiException as e:
        raise e
    except KeyError as e:
        logger.error("Error checking venue has events, key error: %S, ", e)
        raise FixrApiException('Key error', e)
    except IndexError as e:
        logger.error("Error checking venue has events, index error: %S, ", e)
        raise FixrApiException('Index error', e)
    except Exception as e:
        logger.error("Error checking vnue has events, unknown error: %S, ", e)
        raise FixrApiException('unknown error', e)

