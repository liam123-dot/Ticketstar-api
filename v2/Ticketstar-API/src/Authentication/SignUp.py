"""

Ths file will contain the logic for when a user signs up for the platform.

This contains many aspect of error handling and verification.

We need many functions to fulfill this.
"""



"""
SignUpFunction:
Comes from the sign up screen.
Takes the following information in the body:

first_name, last_name, email, phone_number, password

uses the cognito sdk to sign up.

Possible Exceptions that need to be handled due to user error only:
UsernameExistsException, InvalidPasswordException - message returned to user

Error that could be due to the user or Ticketstar:
CodeDeliveryFailureException, error with sending the verification code


Error that is due to Ticketstar:
InvalidEmailRoleAccessPolicyException
InvalidSmsRoleAccessPolicyException

Response from cognito:

{
   "CodeDeliveryDetails": { 
      "AttributeName": "string",
      "DeliveryMedium": "string",
      "Destination": "string"
   },
   "UserConfirmed": boolean,
   "UserSub": "string"
}

"""

def lambda_handler(event, context)
