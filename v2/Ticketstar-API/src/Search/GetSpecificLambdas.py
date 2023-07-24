"""

This is used to get a specific event/organisers/venues info

uses the path parameters

venues /venue/{venue_id}
organisers /organiser?organiser_id=%s&slug=%s this will be determined on the client side
events /event/{event_id}

"""
import json
import logging

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

from FixrExceptions import FixrApiException


def get_event(event, context):
    from Events import get_event_info

    try:
        path_parameters = event['pathParameters']

        event_id = int(path_parameters['event_id'])

    except KeyError as e:

        logger.error("Invalid path parameters, error: %s", e)

        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Invalid path parameters ' + str(e)
            })
        }
    except ValueError as e:

        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Invalid path parameters ' + str(e)
            })
        }

    try:
        query_string_parameters = event['queryStringParameters']

        user_id = query_string_parameters['user_id']

    except KeyError as e:

        logger.error("Invalid path parameters, error: %s", e)

        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Invalid path parameters ' + str(e)
            })
        }

    try:

        response = get_event_info(event_id, user_id)

        return {
            'statusCode': 200,
            'body': json.dumps(
                response
            )
        }

    except FixrApiException as e:
        logger.error("Error with fixr response error: %s. with event: %s", e, event)
        return {
            'statusCode': 501,
            'body': json.dumps({
                'message': 'Internal server error, please try again later',
                'reason': 'FixrGeneralIssue'
            })
        }
    except KeyError as e:
        logger.error("Key error, possible change to ticket parameters, error: %s", str(e))
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Internal server error, please try again later'
            })
        }
    except Exception as e:
        logger.error("Exception get_event, error: %s, event: %s", e, event)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Server error',
                'reason': 'Exception'
            })
        }


def get_organiser_events(event, context):
    from Organisers import get_organiser_events_info
    try:
        query_string_parameters = event['queryStringParameters']

        organiser_id = int(query_string_parameters['organiser_id'])
        slug = query_string_parameters['slug']

    except KeyError as e:

        logger.error("Invalid path parameters, error: %s", e)

        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Invalid path parameters ' + str(e)
            })
        }
    except ValueError as e:

        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Invalid path parameters ' + str(e)
            })
        }

    try:

        data = get_organiser_events_info(organiser_id=organiser_id, slug=slug)

    except FixrApiException as e:
        logger.error("Error fetching organiser events, error: %s,\n events: %s", str(e), event)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Internal Server Error, please try again later',
                'reason': 'Exception',
            })
        }
    except Exception as e:
        logger.error("Exception get_organiser_events, error: %s, event: %s", e, event)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Server error',
                'reason': 'Exception'
            })
        }

    events = []

    try:

        for event in data:
            venue = event['venue']
            events.append({

                'fixr_id': event['id'],
                'name': event['name'],
                'image_url': event['eventImage'],
                'venue': {
                    'id': venue['id'],
                    'name': venue['name'],
                    'city': venue['city']
                },
                'sold_out': event['soldOut'],
                'cheapest_ticket': event['cheapestTicket'],
                'open_time': event['openTime']

            })

        return {
            'statusCode': 200,
            'body': json.dumps({
                'events': events
            })
        }

    except Exception as e:
        logger.error("Error compiling events dict, error: %s, event: %s", e, events)

        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Internal Server Error, please try again later',
                'reason': 'Exception',
            })
        }


def get_venue_events(event, context):
    from Venues import get_venue_events
    try:
        path_parameters = event['pathParameters']

        venue_id = int(path_parameters['venue_id'])

    except KeyError as e:

        logger.error("Invalid path parameters, error: %s", e)

        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Invalid path parameters ' + str(e)
            })
        }
    except ValueError as e:

        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Invalid path parameters ' + str(e)
            })
        }

    try:
        data = get_venue_events(venue_id)
    except FixrApiException as e:
        logger.info("Error with fixr response error: %s. with event: %s", e, event)
        return {
            'statusCode': 501,
            'body': json.dumps({
                'message': 'Internal server error, please try again later',
                'reason': 'FixrGeneralIssue'
            })
        }
    except Exception as e:
        logger.info("Exception get_venue_events, error: %s, event: %s", e, event)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Server error',
                'reason': 'Exception'
            })
        }

    parameters_to_pull = ['id', 'name', 'event_image', 'sold_out', 'cheapest_ticket', 'open_time']
    events = []

    for event in data:
        event_info = {}
        for parameter in parameters_to_pull:
            try:
                event_info[parameter] = event[parameter]
            except KeyError as e:
                logger.error("Error with parameter: %s. Error given: %s, ticket data: %s", parameter, e, event)
        events.append(event_info)

    return {
        'statusCode': 200,
        'body': json.dumps({
            'events': events
        })
    }

