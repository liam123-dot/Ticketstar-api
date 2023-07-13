import requests
import json
import logging
import concurrent.futures
from GetTicketBidsAsks import get_bids_asks

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    logger.info("blahjj")
    try:
        queryString = event['queryStringParameters']
    except (KeyError, TypeError):
        return {
            "statusCode": 400,
            "body": json.dumps({
                "message": "Invalid input, no query string provided"
            })
        }

    try:
        event_id = queryString['event_id']
        user_id = queryString['user_id']
    except (KeyError, TypeError):
        return {
            "statusCode": 400,
            "body": json.dumps({
                "message": "Invalid input, invalid query"
            })
        }

    event_url = "https://api.fixr.co/api/v2/app/event/" + str(event_id) + "?"

    response = requests.get(event_url)

    data = response.json()

    if not response.ok:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "message": "Unknown error"
            })
        }

    tickets_response = data['tickets']

    tickets = []
    ticket_parameters_to_pull = ['id', 'name', 'price', 'booking_fee', 'promo_code_required', 'entry_count', 'currency',
                                 'max_per_user', 'sold_out', 'not_yet_valid', 'expired', 'last_entry']

    # Concurrent execution of get_bids_asks
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_ticket = {
            executor.submit(get_bids_asks, ticket['id'], event_id, user_id): ticket for ticket in tickets_response}
        for future in concurrent.futures.as_completed(future_to_ticket):
            ticket = future_to_ticket[future]
            try:
                bids_asks_data = future.result()
                ticket_dict = {}
                for parameter in ticket_parameters_to_pull:
                    ticket_dict[parameter] = ticket[parameter]
                ticket_dict['bids_asks'] = bids_asks_data
                tickets.append(ticket_dict)
            except Exception as e:
                print(f"Exception {e} was raised while getting bids_asks data.")

    tickets = sorted(tickets, key=lambda d: d['id'])

    data = {
            "id": data['id'],
            "name": data['name'],
            "open_time": data['open_time'],
            "close_time": data['close_time'],
            "sold_out": data['sold_out'],
            "venue": data['venue'],
            "tickets": tickets
        }

    response = {
        "statusCode": 200,
        "body": json.dumps(data)
    }

    return response
