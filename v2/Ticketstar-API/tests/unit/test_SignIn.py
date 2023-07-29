import unittest
import json

import botocore.exceptions

from src.Authentication.SignIn import lambda_handler
from unittest.mock import patch

class TestSignIn:

    def setup_method(self, function):
        self.event = {
            'body': json.dumps({
                'email': 'liambuchanan358@yahoo.co.uk',
                'password': 'Password123!'
            })
        }
        self.context = {}

    def test_lambda_handler_input(self):
        mock_event = {
            'body': json.dumps({
                'emai': 'liambuchanan358@yahoo.co.uk',
                'password': 'password'
            })
        }

        response = lambda_handler(mock_event, "")

        assert response['statusCode'] == 400
        assert json.loads(response['body'])['reason'] == 'InvalidBody'

        mock_event = {
            'body': json.dumps({
                'email': 'liambuchanan358@yahoo.co.uk',
                'ssword': 'password'
            })
        }

        response = lambda_handler(mock_event, "")

        assert response['statusCode'] == 400
        assert json.loads(response['body'])['reason'] == 'InvalidBody'

    def test_lambda_handler_initiate_auth(self):
        with patch('src.Authentication.SignIn.get_secret_hash', return_value=True):
            with patch('src.Authentication.SignIn.submit_cognito_initiate_auth', side_effect=botocore.exceptions.ClientError):
                response = lambda_handler(self.event, self.context)
                assert response['statusCode'] == 400
