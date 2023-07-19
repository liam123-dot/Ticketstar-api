"""

File to manage the functions performed on an individual fixr account

"""

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
