import json
from DatabaseConnector import Database
from datetime import datetime, timedelta
import time

def convert_to_epoch(year, month, day, hour=0, minute=0, second=0):
    """Converts a date to epoch timestamp."""
    dt = datetime(year, month, day, hour, minute, second)
    epoch_time = int(time.mktime(dt.timetuple()))
    return epoch_time

def get_interval_seconds(count_by):
    if count_by == "hourly":
        return 3600
    elif count_by == "daily":
        return 86400
    elif count_by == "weekly":
        return 604800
    elif count_by == "monthly":
        return 2592000  # 30 days in seconds

def get_unique_users_for_interval(database, start_date_epoch, end_date_epoch, interval_seconds):
    sql = """
    SELECT open_time DIV %s AS interval_time,
           COUNT(DISTINCT user_id) AS user_count,
           GROUP_CONCAT(DISTINCT user_id) AS user_ids
    FROM Sessions
    WHERE open_time >= %s AND open_time < %s
    GROUP BY interval_time
    """

    results = database.execute_select_query(sql, (interval_seconds, start_date_epoch, end_date_epoch))

    result_data = {}
    for row in results:
        interval_start = row[0] * interval_seconds
        count = row[1]
        user_ids = row[2].split(',')
        human_readable_time = datetime.fromtimestamp(interval_start).strftime('%Y-%m-%d %H:%M:%S')
        result_data[str(interval_start)] = {
            "count": count,
            "start_time_human_readable": human_readable_time,
            "user_ids": user_ids
        }

    return result_data

def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        count_by = body['count_by']
        from_date = body['from_date']
        to_date = body['to_date']
        show_none = body.get('show_none', False)  # Default to False if not provided

        epoch_start_time = convert_to_epoch(from_date['year'], from_date['month'], from_date['day'])
        epoch_end_time = convert_to_epoch(to_date['year'], to_date['month'], to_date['day'])

        # Adjust epoch_end_time if it's in the future
        current_epoch_time = int(time.time())
        if epoch_end_time > current_epoch_time:
            epoch_end_time = current_epoch_time

        if count_by not in ["hourly", "daily", "weekly", "monthly"]:
            raise ValueError(f"Invalid count_by value: {count_by}")

        interval_seconds = get_interval_seconds(count_by)

        with Database() as database:
            result_data = get_unique_users_for_interval(database, epoch_start_time, epoch_end_time, interval_seconds)

        # Filter out the intervals with zero counts if show_none is False
        if not show_none:
            result_data = {key: val for key, val in result_data.items() if val["count"] > 0}

    except KeyError as e:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Invalid body: ' + str(e)
            })
        }

    return {
        'statusCode': 200,
        'body': json.dumps({
            'unique_users_counts': result_data
        })
    }
