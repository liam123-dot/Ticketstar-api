import requests
import json


def lambda_handler(event, context):

    try:
        # Extracting query parameters from the event object
        slug = event['queryStringParameters']['slug']
        organiser_id = event['queryStringParameters']['organiser_id']

    except KeyError:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "message": "Invalid query parameters"
            })
        }

    events = get_organiser_events(slug, organiser_id)

    return {
        'statusCode': 200,
        'body': json.dumps(events)
    }


def get_organiser_events(slug, organiser_id):
    url = 'https://fixr.co'

    search_term = "{\"props\":"

    response = requests.get(url)

    text = response.text

    index = text.find(search_term)

    counter = 0

    open_counter = 0
    close_counter = 0

    while True:
        if text[index + counter] == '{':
            open_counter += 1
        elif text[index + counter] == '}':
            close_counter += 1

        counter += 1

        if open_counter == close_counter and open_counter != 0:
            break

    data = json.loads(text[index: index + counter])

    buildId = data['buildId']

    if slug is not None:
        url = f"https://fixr.co/_next/data/{buildId}/en-GB/organiser/{slug}.json?id={slug}"
    else:
        url = f"https://fixr.co/_next/data/{buildId}/en-GB/organiser/{organiser_id}.json?id={organiser_id}"

    response = requests.get(url)

    data = response.json()['pageProps']['data']['data']

    events = []

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

    return events
