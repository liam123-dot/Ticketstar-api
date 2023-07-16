# Ticketstar-API


Status Code Responses

```

400 - Don't display returned message to user
401 - Display returned message to user

500 - server error
501 - server error and display to user

```

When a response is made to the client and there is an error we have some custom defined 'reasons'.

a valid reason

```

Exception

FixrGeneralIssue
FixrJsonDecode
FixrBadResponse

InvalidQueryString
InvalidBody
InvalidBodyJson

InvalidUserInput

CognitoException
CognitoTooManyRequests
SecretHashGenerator

CodeDeliveryFailureException
CodeMismatchException

UserNotFoundException

```
