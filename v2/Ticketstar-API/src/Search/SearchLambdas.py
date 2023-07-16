import logging
import json

logger = logging.getLogger()
logger.setLevel(logging.INFO)

from Events import search as event_search
from Venues import search as venue_search
from Organisers import search as organiser_search


def generic_get(search_function, entity_type, event, context):
    try:
        query_string = event['queryStringParameters']
        query = query_string['query']

    except KeyError as e:
        logger.error(f"Invalid query string passed, error: {e}, event: {event}")
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': f'Invalid query string sent: {e}',
                'reason': 'InvalidQueryString'
            })
        }

    limit, offset = query_string.get('limit'), query_string.get('offset')

    try:
        entities = search_function(query, limit=limit, offset=offset)

    except Exception as e:
        logger.error(f"Error searching for {entity_type}, error: {e}")
        return {
            'statusCode': 500,  # Changed from 401 to 500 as this is a server error
            'body': json.dumps({
                'message': 'Server error, please try again',
                'reason': 'Exception',
                'error': type(e).__name__
            })
        }

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f'Successful search for {entity_type}',
            entity_type: entities
        })
    }


def get_events(event, context):
    return generic_get(event_search, 'events', event, context)


def get_venues(event, context):
    return generic_get(venue_search, 'venues', event, context)


def get_organisers(event, context):
    return generic_get(organiser_search, 'organisers', event, context)
