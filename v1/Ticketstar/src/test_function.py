from DatabaseConnector import function


def lambda_handler(event, context):
    return {
        'statusCode': 200,
        'body': function()
    }
