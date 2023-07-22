"""

File to manage the functions performed on an individual fixr account

"""
import json

import requests
from FixrExceptions import FixrApiException


class FixrAccount:

    def __init__(self, session: requests.session(), username, password):
        self.auth_token = None
        self.session = session
        self.username = username
        self.password = password

        self.login()

    def login(self):
        login_url = "https://api.fixr.co/api/v2/app/user/authenticate/with-email"
        login_body = {
            'email': self.username,
            'password': self.password
        }

        response = self.session.post(login_url, json=login_body)
        if not response.ok:
            raise FixrApiException("Invalid response from login api")

        data = response.json()

        self.auth_token = data['auth_token']

    def claim_ticket(self, transfer_url):
        verify_transfer_headers = {
            'Accept': 'application/json',
            'Authorization': 'Token ' + self.auth_token
        }

        code = transfer_url.split("/")[-1]

        verify_transfer_url = "https://api.fixr.co/api/v2/app/transfer-ticket/" + code

        response = self.session.post(verify_transfer_url, headers=verify_transfer_headers, json={})

        if not response.ok:
            data = response.json()
            if data['message'] == "They are already your tickets! You can cancel your transfer from your profile if" \
                                  " you have changed your mind and still want them.":
                pass
            else:
                raise FixrApiException("Error claiming transfer url")

        data = response.json()

        ticket_reference = data['data']['transfer_code']['transferred_ticket_reference']

        return ticket_reference

    def get_ticket_with_reference(self, ticket_reference):
        url = f"https://api.fixr.co/api/v2/app/booking/{ticket_reference}"

        headers = {
            'Authorization': 'Token ' + self.auth_token,
        }

        response = requests.get(url, headers=headers)

        if not response.ok:
            if response.status_code == 404:
                return None

            raise FixrApiException("Error claiming ticket")

        return response.json()

    def get_transfer_url(self, ticket_reference):
        ticket_data = self.get_ticket_with_reference(ticket_reference)

        if not ticket_data['is_transferable']:
            transfer_url = ticket_data['transfer_url']
            if transfer_url is not None:
                return transfer_url
        else:
            url = f"https://api.fixr.co/api/v2/app/booking/{ticket_reference}/transfer-code"
            headers = {
                'Authorization': 'Token ' + self.auth_token
            }
            response = self.session.post(url, headers=headers)

            if not response.ok:
                raise FixrApiException("Invalid fixr response")

            transfer_url = response.json()['transfer_url']

            return transfer_url

    def check_ownership(self, ticket_reference):
        url = "https://api.fixr.co/api/v2/app/booking?only=future&limit=999"
        headers = {
            "Authorization": 'Token ' + self.auth_token
        }
        response = self.session.get(url, headers=headers)
        if not response.ok:
            raise FixrApiException

        data = response.json()['data']

        for ticket in data:
            if ticket['reference_id'] == ticket_reference:
                return True

        return False