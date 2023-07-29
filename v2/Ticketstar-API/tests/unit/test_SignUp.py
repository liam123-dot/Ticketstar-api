import unittest
from unittest.mock import Mock, patch
from src.Authentication.SignUp import check_phone_number_valid, lambda_handler
import json
import botocore

class TestSignUp(unittest.TestCase):

    @patch('src.Authentication.SignUp.cognito')
    def test_check_phone_number_valid(self, mock_cognito):
        # Create a mock response that simulates what `list_users` would return
        mock_response = {
            'Users': []
        }

        # Configure the mock to return the mock response when it is called
        mock_cognito.list_users.return_value = mock_response

        # Call the function with a test phone number
        phone_number = '+1234567890'
        result = check_phone_number_valid(phone_number)

        # Check that the function returned True, as there are no users with the phone number
        self.assertTrue(result)

        # Now, configure the mock to simulate a user with the phone number existing
        mock_response = {
            'Users': [
                {
                    'Attributes': [
                        {
                            'Name': 'phone_number',
                            'Value': phone_number
                        }
                    ]
                }
            ]
        }
        mock_cognito.list_users.return_value = mock_response

        # Call the function again
        result = check_phone_number_valid(phone_number)

        # This time, the function should return False, as a user with the phone number exists
        self.assertFalse(result)

    def setup_method(self, function):
        self.event = {
            'body': json.dumps({
                'email': 'test@example.com',
                'password': 'Test1234',
                'firstName': 'John',
                'lastName': 'Doe',
                'phoneNumber': '+1234567890'
            })
        }
        self.context = {}

    def test_lambda_handler_valid(self):
        with patch('src.Authentication.SignUp.check_phone_number_valid', return_value=True):
            with patch('src.Authentication.SignUp.submit_cognito_sign_up', return_value="EMAIL"):
                response = lambda_handler(self.event, self.context)
                assert response['statusCode'] == 200
                assert json.loads(response['body'])['message'] == 'User successfully registered'
                assert json.loads(response['body'])['confirmation_method'] == 'EMAIL'

    def test_lambda_handler_invalid_phone(self):
        with patch('src.Authentication.SignUp.check_phone_number_valid', return_value=False):
            response = lambda_handler(self.event, self.context)
            assert response['statusCode'] == 401
            assert json.loads(response['body'])['message'] == 'An account already exists with the provided phone number'
            assert json.loads(response['body'])['reason'] == 'InvalidUserInput'

    def test_lambda_handler_cognito_exception(self):
        with patch('src.Authentication.SignUp.check_phone_number_valid', return_value=True):
            with patch('src.Authentication.SignUp.submit_cognito_sign_up', side_effect=botocore.exceptions.ClientError(
                    {'Error': {'Code': 'UsernameExistsException', 'Message': 'User already exists'}}, 'sign_up')):
                response = lambda_handler(self.event, self.context)
                assert response['statusCode'] == 401
                assert json.loads(response['body'])['message'] == 'User already exists'
                assert json.loads(response['body'])['reason'] == 'CognitoException'
                assert json.loads(response['body'])['error'] == 'UsernameExistsException'


if __name__ == '__main__':
    unittest.main()
