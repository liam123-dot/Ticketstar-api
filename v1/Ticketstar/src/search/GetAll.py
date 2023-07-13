
import requests
import json

from GetVenueEvents import get_venue_events
from GetOrganiserEvents import get_organiser_events

headers = {
    "Accept": "application/json; version=3.0"
}

import concurrent.futures


def lambda_handler(event, context):
    '''

    Used for the search bar

    :param event:

        Inside the body there will be a json component with the search contents

    :param context:
    :return:

        A dictionary containing information about relevant events, venues and organiser for users to select

    '''
    try:
        query_string = event['multiValueQueryStringParameters']
    except (KeyError, TypeError):
        return {
            "statusCode": 400,
            "body": json.dumps({
                "message": "Invalid input, no query string provided"
            })
        }

    try:
        query = query_string['query'][0]
    except (KeyError, TypeError):
        return {
            "statusCode": 400,
            "body": json.dumps({
                "message": "Invalid input, invalid query"
            })
        }

    # Use ThreadPoolExecutor to run functions concurrently
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(get_events, query): 'events',
            executor.submit(get_venues, query): 'venues',
            executor.submit(get_organisers, query): 'organisers'
        }

        results = {}

        for future in concurrent.futures.as_completed(futures):
            key = futures[future]
            try:
                results[key] = future.result()
            except Exception as exc:
                print(f'{key} generated an exception: {exc}')

    response = {
        "statusCode": 200,
        "body": json.dumps({
            "events": results.get('events', [])[:3],
            "venues": results.get('venues', []),
            "organisers": results.get('organisers', [])
        })
    }

    return response


def get_events(query):
    events_url = f"https://api.fixr.co/search/events?query={query}&limit=3&offset=0&popularity__boost=0"
    events = []

    response = requests.get(events_url, headers=headers)

    if not response.ok:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "message": "Unknown error with events url"
            })
        }

    data = response.json()

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

    return events


def get_venues(query):
    venues_url = f"https://api.fixr.co/search/venues?query={query}&limit=6&offset=0&popularity__boost=0"

    response = requests.get(venues_url, headers=headers)

    if not response.ok:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "message": "Unknown error with venues url"
            })
        }

    data = response.json()

    venues = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_venue = {executor.submit(get_venue_events, venue['id']): venue for venue in data['results']}

        for future in concurrent.futures.as_completed(future_to_venue):
            venue = future_to_venue[future]
            venue_events = future.result()

            if venue_events:
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


def get_organisers(query):
    organisers_url = f"https://api.fixr.co/search/organisers?query={query}&limit=6&offset=0&popularity__boost=0"

    response = requests.get(organisers_url, headers=headers)

    if not response.ok:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "message": "Unknown error with organisers url"
            })
        }

    data = response.json()

    organisers = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_organiser = {executor.submit(get_organiser_events, organiser['slug'], organiser['id']): organiser for organiser in data['results']}

        for future in concurrent.futures.as_completed(future_to_organiser):
            organiser = future_to_organiser[future]
            organiser_events = future.result()

            if organiser_events:
                organisers.append({
                    'fixr_id': organiser['id'],
                    'name': organiser['name'],
                    'image_url': organiser['image_url'],
                    'slug': organiser['slug']
                })

            if len(organisers) == 3:
                break

    return organisers
