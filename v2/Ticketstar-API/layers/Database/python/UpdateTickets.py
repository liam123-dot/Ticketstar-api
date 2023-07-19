from DatabaseActions import get_tickets_to_update, update_ticket_info
import requests

def update():
    tickets = get_tickets_to_update()

    for ticket in tickets:
        ticket_id = ticket[0]
        fixr_ticket_id = ticket[1]
        fixr_event_id = ticket[2]

        get_event_url = f"https://api.fixr.co/api/v2/app/event/{fixr_event_id}?"

        response = requests.get(get_event_url)

        if response.ok:
            data = response.json()

            event_name = data['name']
            open_time = data['open_time']
            close_time = data['close_time']
            image_url = data['event_image']
            ticket_name = ""

            for ticket in data['tickets']:
                if ticket['id'] == fixr_ticket_id:
                    ticket_name = ticket['name']

            update_ticket_info(ticket_name, event_name, open_time, close_time, image_url, ticket_id)