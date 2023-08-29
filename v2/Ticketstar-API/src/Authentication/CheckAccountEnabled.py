
import json

import boto3
from GetCognitoCreds import get_secret


def lambda_handler(event, context):

    user_pool_id = get_secret()['USER_POOL_ID']

    body = json.loads(event['body'])
    user_id = body['user_id']

    cognito = boto3.client('cognito-idp')
    response = cognito.admin_get_user(
        UserPoolId=user_pool_id,
        Username=user_id
    )

    return {
        'statusCode': 200,
        'body': json.dumps({
            'enabled': response['Enabled']
        })
    }
