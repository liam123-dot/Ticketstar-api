import requests
import json


def lambda_handler(event, context):

    try:

        event_id = event['queryStringParameters']['event_id']

    except KeyError:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'missing query parameters'
            })
        }

    events = get_venue_events(event_id)

    return {
        'statusCode': 200,
        'body': json.dumps(events)
    }


def get_venue_events(event_id):
    url = f"https://api.fixr.co/api/v2/app/venue/{event_id}?"

    response = requests.get(url)

    data = response.json()

    events = []

    for event in data['events']:
        events.append({
            'fixr_id': event['id'],
            'name': event['name'],
            'image_url': event['event_image'],
            'sold_out': event['sold_out'],
            'cheapest_ticket': event['cheapest_ticket'],
            'open_time': event['open_time']
        })

    return events
