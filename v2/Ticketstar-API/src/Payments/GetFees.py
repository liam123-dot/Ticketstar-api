
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
        get_fees_sql = "SELECT stripe_fixed_fee, stripe_variable_fee, platform_fixed_fee, platform_variable_fee, pricing_id FROM Fees"

        results = database.execute_select_query(get_fees_sql)[0]

        stripe_fixed_fee = results[0]
        stripe_variable_fee = results[1]

        platform_fixed_fee = results[2]
        platform_variable_fee = results[3]

        fees = {
            'stripe_fixed_fee': stripe_fixed_fee,
            'stripe_variable_fee': stripe_variable_fee,
            'platform_fixed_fee': platform_fixed_fee,
            'platform_variable_fee': platform_variable_fee,
        }
        return fees