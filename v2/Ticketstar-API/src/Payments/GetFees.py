
"""

Fetches the current fees from database

"""
import json

from DatabaseConnector import Database
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    try:

        query_string_parameters = event['queryStringParameters']
        if 'ask_id' in query_string_parameters:
            ask_id = query_string_parameters['ask_id']
            return {
                'statusCode': 200,
                'body': json.dumps(get_fees_by_ask_id(ask_id))
            }
        else:

            return {
                'statusCode': 200,
                'body': json.dumps(get_fees())
            }

    except Exception as e:
        logger.error("Error getting fees, %s", e)
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Error getting fees',
                'reason': str(e)
            })
        }

def get_fees():
    with Database() as database:
        get_fees_sql = """
        SELECT stripe_fixed_fee, stripe_variable_fee, platform_fixed_fee, platform_variable_fee, pricing_id 
        FROM Fees
        ORDER BY pricing_id DESC
        LIMIT 1
        """

        results = database.execute_select_query(get_fees_sql)[0]

        stripe_fixed_fee = results[0]
        stripe_variable_fee = results[1]
        platform_fixed_fee = results[2]
        platform_variable_fee = results[3]
        pricing_id = results[4]  # Use index 4 for pricing_id since it starts at 0

        fees = {
            'pricing_id': pricing_id,
            'stripe_fixed_fee': stripe_fixed_fee,
            'stripe_variable_fee': stripe_variable_fee,
            'platform_fixed_fee': platform_fixed_fee,
            'platform_variable_fee': platform_variable_fee,
        }
        return fees

def get_fees_by_ask_id(ask_id):
    get_fees_sql = """
    SELECT
    f.stripe_fixed_fee,
    f.stripe_variable_fee,
    f.platform_fixed_fee,
    f.platform_variable_fee,
    a.pricing_id
    FROM
        asks a
    JOIN
        Fees f
    ON
        a.pricing_id = f.pricing_id
    WHERE
    a.ask_id = %s;
    """
    with Database() as database:
        results = database.execute_select_query(get_fees_sql, (ask_id, ))[0]

        stripe_fixed_fee = results[0]
        stripe_variable_fee = results[1]
        platform_fixed_fee = results[2]
        platform_variable_fee = results[3]
        pricing_id = results[4]  # Use index 4 for pricing_id since it starts at 0

        fees = {
            'pricing_id': pricing_id,
            'stripe_fixed_fee': stripe_fixed_fee,
            'stripe_variable_fee': stripe_variable_fee,
            'platform_fixed_fee': platform_fixed_fee,
            'platform_variable_fee': platform_variable_fee,
        }

        return fees
