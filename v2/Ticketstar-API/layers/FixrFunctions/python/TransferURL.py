"""

This file will contain functions that are to do with transfer urls.

"""
from FixrExceptions import FixrApiException
from FixrAccount import FixrAccount
import json
import requests
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def verify_transfer_url(transfer_url, fixr_event_id, fixr_ticket_id):
    response = requests.get(transfer_url)

    if not response.ok:
        raise FixrApiException("Request not ok")

    try:

        search_term = "pageProps"

        index = response.text.index(search_term)
        text = response.text[index + len(search_term) + 2:]

        open_brackets = 0
        close_brackets = 0

        for i in range(0, len(text)):
            if text[i] == '{':
                open_brackets += 1
            elif text[i] == '}':
                close_brackets += 1

            if open_brackets == close_brackets:
                break

        data = json.loads(text[:i + 1])

        data = data['data']['data']

    except Exception as e:
        raise FixrApiException(e)

    ticket_reference = data['ticketReference']

    ticket_number = ticket_reference['numberOfTickets']

    if ticket_number != 1:
        pass

    transfer_event_id = ticket_reference['event']['id']
    transfer_ticket_id = ticket_reference['ticketType']['id']

    return transfer_event_id == fixr_event_id and transfer_ticket_id == fixr_ticket_id


def claim_ticket(transfer_url, ticket_id):
    from DatabaseActions import get_fixr_account_for_ticket_id
    from FixrAccount import FixrAccount

    account_details = get_fixr_account_for_ticket_id(ticket_id)

    username = account_details[0]
    password = account_details[1]
    account_id = account_details[2]

    with requests.session() as s:
        account = FixrAccount(s, username, password)

        ticket_reference = account.claim_ticket(transfer_url)

        return account_id, ticket_reference


def get_transfer_url(fixr_username, fixr_password, ticket_reference):
    with requests.session() as s:
        account = FixrAccount(s, fixr_username, fixr_password)
        transfer_url = account.get_transfer_url(ticket_reference)

        return transfer_url
