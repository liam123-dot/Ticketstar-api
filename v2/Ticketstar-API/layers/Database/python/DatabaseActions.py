"""

Functions that contain all the sql queries that are needed and commonly used across the api

"""
from DatabaseConnector import Database
from DatabaseException import DatabaseException
import logging


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_ticket_id(fixr_event_id, fixr_ticket_id):

    try:

        with Database() as database:

            get_ticket_query = "SELECT ticket_id, search_count FROM tickets WHERE fixr_ticket_id=%s AND fixr_event_id=%s"

            result = database.execute_select_query(get_ticket_query, (fixr_ticket_id, fixr_event_id))

            if len(result) == 0:

                insert_ticket_query = "INSERT INTO tickets(fixr_ticket_id, fixr_event_id) VALUES (%s, %s)"

                ticket_id = database.execute_insert_query(insert_ticket_query, (fixr_ticket_id, fixr_event_id))

            else:

                ticket_id = result[0][0]

                search_count = int(result[0][1]) + 1

                update_search_query = "UPDATE tickets SET search_count=%s WHERE ticket_id=%s"

                database.execute_update_query(update_search_query, (search_count, ticket_id))

        return ticket_id

    except Exception as e:
        logger.error("Error get_ticket_id, error: %s", e)
        raise DatabaseException(e)


def get_asks_by_ticket_id(ticket_id):
    get_asks_query = """SELECT ask_id, price, seller_user_id, reserved, reserve_timeout, buyer_user_id from Asks
    WHERE ticket_id=%s AND fulfilled=0 AND listed=1 ORDER BY price ASC"""

    try:

        with Database() as database:

            result = database.execute_select_query(get_asks_query, (ticket_id ,))

            asks = []

            if len(result) == 0:
                return {
                    'ask_count': 0,
                    'asks': asks
                }

            for ask in result:
                asks.append({
                    'ask_id': ask[0],
                    'price': ask[1],
                    'seller_user_id': ask[2],
                    'reserved': ask[3] == b'\x01',
                    'reserve_timeout': ask[4],
                    'buyer_user_id': ask[5]
                })

        return {
            'ask_count': len(asks),
            'asks': asks
        }

    except Exception as e:
        logger.error("Error get_asks_by_ticket_id, error: %s", e)
        raise DatabaseException(e)


def get_asks_by_fixr_ids(fixr_event_id, fixr_ticket_id):
    ticket_id = get_ticket_id(fixr_event_id, fixr_ticket_id)

    return ticket_id, get_asks_by_ticket_id(ticket_id)


def get_ask(ask_id):
    query = """SELECT price, fulfilled, reserved, buyer_user_id, reserve_timeout FROM asks where ask_id=%s """

    try:
        with Database() as database:
            result = database.execute_select_query(query, (ask_id, ))

        if len(result) == 0:
            return None

        ask = result[0]

        ask = {
            'price': ask[0],
            'fulfilled': ask[1] == b'\x01',
            'reserved': ask[2] == b'\x01',
            'buyer_user_id': ask[3],
            'reserve_timeout': ask[4]
        }

        return ask

    except Exception as e:
        logger.error("Error get_ask, error: %s", e)
        raise DatabaseException(e)


def reserve_ask(ask_id, user_id, reserve_timeout):
    query = """UPDATE asks SET reserved=1, reserve_timeout=%s, buyer_user_id=%s WHERE ask_id=%s"""

    try:
        with Database() as database:
            database.execute_update_query(query, (reserve_timeout, user_id, ask_id))

    except Exception as e:
        logger.error("Error get_ask, error: %s", e)
        raise DatabaseException(e)
