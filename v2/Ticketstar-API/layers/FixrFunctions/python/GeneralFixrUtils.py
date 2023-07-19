
"""

Contains some useful functions

"""

def get_ticket_max(fixr_event_id, fixr_ticket_id):
    import requests
    import FixrExceptions

    url = f"https://api.fixr.co/api/v2/app/event/{fixr_event_id}"

    response = requests.get(url)

    if not response.ok:
        raise FixrExceptions.FixrApiException("Error getting event")

    data = response.json()

    for ticket in data['tickets']:
        if ticket['id'] == fixr_ticket_id:
            return ticket['max_per_user']
