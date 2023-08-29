import boto3
from botocore.exceptions import NoCredentialsError
from DatabaseConnector import Database
import json

def lambda_handler(event, context):

    try:

        body = json.loads(event['body'])
        ask_id = body['ask_id']

    except KeyError as e:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'invalid parameters: ' + str(e)
            })
        }

    get_ticket_reference_sql = """
    SELECT rt.ticket_reference
    FROM asks AS a
    JOIN realtickets AS rt ON a.real_ticket_id = rt.real_ticket_id
    WHERE a.ask_id = %s;

    """

    with Database() as database:
        results = database.execute_select_query(get_ticket_reference_sql, (ask_id, ))

        return {
            'statusCode': 200,
            'body': json.dumps({
                'url': generate_presigned_url(results[0][0])
            })
        }


def generate_presigned_url(ticket_reference, bucket_name="api-2-pdfbucket-1e7y72t39nzqk", expiration=3600):

    object_name = 'pdf-' + str(ticket_reference) + '.pdf'

    """
    Generate a presigned URL to share an S3 object

    :param bucket_name: string
    :param object_name: string
    :param expiration: Time in seconds for which the presigned URL is valid
    :return: Presigned URL as string. If error, returns None.
    """

    s3_client = boto3.client('s3')
    try:
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': object_name,
                                                            'ResponseContentDisposition': 'inline; filename=' + object_name},
                                                    ExpiresIn=expiration)
    except NoCredentialsError:
        print('Credentials not available')
        return None

    return response


