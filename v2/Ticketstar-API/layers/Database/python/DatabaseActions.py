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

            get_ticket_query = "SELECT ticket_id FROM tickets WHERE fixr_ticket_id=%s AND fixr_event_id=%s"

            result = database.execute_select_query(get_ticket_query, (fixr_ticket_id, fixr_event_id))

            if len(result) == 0:

                insert_ticket_query = "INSERT INTO tickets(fixr_ticket_id, fixr_event_id) VALUES (%s, %s)"

                ticket_id = database.execute_insert_query(insert_ticket_query, (fixr_ticket_id, fixr_event_id))

                from UpdateTickets import update

                update()

            else:

                ticket_id = result[0][0]

        return ticket_id

    except Exception as e:
        logger.error("Error get_ticket_id, error: %s", e)
        raise DatabaseException(e)


def get_asks_by_ticket_id(ticket_id):
    get_asks_query = """SELECT ask_id, price, seller_user_id, reserved, reserve_timeout, buyer_user_id from Asks
    WHERE ticket_id=%s AND fulfilled=0 and listed=1 ORDER BY price ASC"""

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
    query = """SELECT price, fulfilled, reserved, buyer_user_id, reserve_timeout, seller_user_id FROM asks where ask_id=%s """

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
            'reserve_timeout': ask[4],
            'seller_user_id': ask[5]
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


def get_fixr_account_for_ticket_id(ticket_id):
    query = """
        SELECT fixr_username, fixr_password, account_id
        FROM fixraccounts
        WHERE account_id IN (
            SELECT account_id
            FROM currentaccountrelationships
            WHERE ticket_id = %s AND quantity < ticket_limit
            UNION
            SELECT account_id
            FROM fixraccounts
            WHERE account_id NOT IN (
                SELECT account_id
                FROM currentaccountrelationships
            )
        )
        LIMIT 1;
        """
    try:
        with Database() as database:
            result = database.execute_select_query(query, (ticket_id, ))
            return result[0]
    except Exception as e:
        raise DatabaseException(e)


def check_relationship_exists(account_id, ticket_id):

    sql = """
    SELECT relationship_id, quantity
    FROM currentAccountRelationships
    WHERE account_id=%s AND ticket_id=%s
    """
    try:
        with Database() as database:
            result = database.execute_select_query(sql, (account_id, ticket_id))
            if len(result) == 0:
                return False
            else:
                relationship_id = result[0][0]
                quantity = result[0][1] + 1
                sql = """
                UPDATE currentAccountRelationships
                SET quantity=%s
                WHERE relationship_id=%s
                """
                database.execute_update_query(sql, (quantity, relationship_id))

                return True

    except Exception as e:
        raise DatabaseException(e)

def create_new_relationship(account_id, ticket_id, max_per_user):
    sql = """
    INSERT INTO currentAccountRelationships(account_id, ticket_id, ticket_limit, quantity)
    VALUES (%s, %s, %s, 1)
    """
    try:
        with Database() as database:
            database.execute_insert_query(sql, (account_id, ticket_id, max_per_user))

    except Exception as e:
        raise DatabaseException(e)


def create_real_ticket(ticket_id, account_id, ticket_reference):
    sql = """
    INSERT INTO realtickets(ticket_id, account_id, ticket_reference)
    VALUES (%s, %s, %s)
    """

    try:
        with Database() as database:
            real_ticket_id = database.execute_insert_query(sql, (ticket_id, account_id, ticket_reference))
            return real_ticket_id

    except Exception as e:
        raise DatabaseException(e)


def create_ask(seller_user_id, price, real_ticket_id, ticket_id):
    sql = """
    INSERT INTO asks(seller_user_id, price, real_ticket_id, ticket_id)
    VALUES (%s, %s, %s, %s)
    """
    try:
        with Database() as database:
            database.execute_insert_query(sql, (seller_user_id, price, real_ticket_id, ticket_id))

    except Exception as e:
        raise DatabaseException(e)


def get_purchases(user_id):
    sql = """
    SELECT ask_id, price, ticket_id, claimed, real_ticket_id FROM asks 
    WHERE buyer_user_id=%s AND fulfilled=1
    """
    try:
        with Database() as database:
            results = database.execute_select_query(sql, (user_id, ))

        return results
    except Exception as e:
        raise DatabaseException(e)


def get_listings(user_id):
    sql = """
    SELECT ask_id, price, ticket_id, fulfilled, listed, real_ticket_id FROM asks
    WHERE seller_user_id=%s
    """
    try:
        with Database() as database:
            results = database.execute_select_query(sql, (user_id, ))

        return results
    except Exception as e:
        raise DatabaseException(e)

def get_ticket_info(ticket_id):
    sql = """SELECT ticket_name, event_name, open_time, close_time, image_url, fixr_event_id, fixr_ticket_id
    from Tickets WHERE ticket_id=%s"""

    try:
        with Database() as database:
            results = database.execute_select_query(sql, (ticket_id, ))

        return results

    except Exception as e:
        raise DatabaseException(e)


def get_tickets_to_update():
    sql = """
    SELECT ticket_id, fixr_ticket_id, fixr_event_id FROM Tickets
    WHERE image_url is NULL
    """

    try:
        with Database() as database:
            results = database.execute_select_query(sql)
        return results
    except Exception as e:
        raise DatabaseException(e)


def update_ticket_info(ticket_name, event_name, open_time, close_time, image_url, ticket_id):
    sql = """
    UPDATE Tickets SET ticket_name=%s, event_name=%s, open_time=%s, close_time=%s, image_url=%s
    WHERE ticket_id=%s
    """
    try:
        with Database() as database:
            database.execute_update_query(sql, (ticket_name, event_name, open_time, close_time, image_url, ticket_id))
    except Exception as e:
        raise DatabaseException(e)


def remove_listing(ask_id):
    sql = """
    UPDATE asks SET listed=0 WHERE ask_id=%s
    """

    try:
        with Database() as database:
            database.execute_update_query(sql, (ask_id, ))
    except Exception as e:
        raise DatabaseException(e)


def relist_listing(ask_id):
    sql = """
        UPDATE asks SET listed=1 WHERE ask_id=%s
        """

    try:
        with Database() as database:
            database.execute_update_query(sql, (ask_id,))
    except Exception as e:
        raise DatabaseException(e)


def edit_listing(ask_id, price):
    sql = """
    UPDATE asks SET price=%s WHERE ask_id=%s
    """
    try:
        with Database() as database:
            database.execute_update_query(sql, (price, ask_id))

    except Exception as e:
        raise DatabaseException(e)


def get_fixr_account_details_from_account_id(account_id):
    sql = """
    SELECT fixr_username, fixr_password FROM FixrAccounts WHERE account_id=%s
    """
    try:
        with Database() as database:
            results = database.execute_select_query(sql, (account_id, ))
        return results
    except Exception as e:
        raise DatabaseException(e)


def get_fixr_account_details_from_real_ticket_id(real_ticket_id):
    sql = """
    SELECT account_id FROM realtickets WHERE real_ticket_id=%s
    """
    try:
        with Database() as database:
            results = database.execute_select_query(sql, (real_ticket_id, ))

        account_id = results[0][0]
        return account_id, get_fixr_account_details_from_account_id(account_id)
    except Exception as e:
        raise DatabaseException(e)


def get_real_ticket_details(real_ticket_id):
    sql = """
    SELECT account_id, ticket_reference FROM realtickets WHERE real_ticket_id=%s
    """
    try:
        with Database() as database:
            results = database.execute_select_query(sql, (real_ticket_id, ))

        real_ticket = results[0]
        return real_ticket
    except Exception as e:
        raise DatabaseException(e)


def get_real_ticket_by_ask_id(ask_id):
    sql = """
    SELECT real_ticket_id FROM asks WHERE ask_id=%s
    """
    try:
        with Database() as database:
            results = database.execute_select_query(sql, (ask_id, ))

        real_ticket_id = results[0][0]
        return get_real_ticket_details(real_ticket_id)
    except Exception as e:
        raise DatabaseException(e)


def get_ticket_ownership(real_ticket_id):
    sql = """
    SELECT ownership_verified, account_id, ticket_reference FROM realtickets WHERE real_ticket_id=%s
    """
    try:
        with Database() as database:
            results = database.execute_select_query(sql, (real_ticket_id, ))

        results = results[0]
        return results
    except Exception as e:
        raise DatabaseException(e)


def update_ticket_ownership(real_ticket_id, ownership):
    sql = """
    UPDATE realtickets SET ownership_verified=%s WHERE real_ticket_id=%s
    """

    try:
        with Database() as database:
            database.execute_update_query(sql, (ownership, real_ticket_id))
    except Exception as e:
        raise DatabaseException(e)


def remove_relationship(account_id, ticket_id):
    sql = """
    UPDATE currentaccountrelationships 
    SET quantity = quantity - 1 
    WHERE account_id = %s AND ticket_id = %s;
    """
    try:
        with Database() as database:
            database.execute_update_query(sql, (account_id, ticket_id))
    except Exception as e:
        raise DatabaseException(e)


def get_ticket_reference_by_real_ticket_id(real_ticket_id):
    sql = """
    SELECT ticket_reference FROM realtickets WHERE real_ticket_id=%s
    """
    try:
        with Database() as database:
            result = database.execute_select_query(sql, (real_ticket_id, ))

        return result[0][0]
    except Exception as e:
        raise DatabaseException(e)


def mark_ask_as_claimed(ask_id):
    sql = """
    UPDATE asks SET claimed=1 WHERE ask_id=%s
    """
    try:
        with Database() as database:
            database.execute_update_query(sql, (ask_id, ))
    except Exception as e:
        raise DatabaseException(e)


def get_customer(user_id):
    sql = "SELECT customer_id FROM stripe WHERE user_id=%s"
    try:
        with Database() as database:
            result = database.execute_select_query(sql, (user_id, ))

        return result
    except Exception as e:
        raise DatabaseException(e)


def create_customer(user_id, stripe_id):
    sql = "INSERT INTO stripe(user_id, customer_id) VALUES(%s, %s)"

    try:
        with Database() as database:
            result = database.execute_insert_query(sql, (user_id, stripe_id))

        return result
    except Exception as e:
        raise DatabaseException(e)

def fulfill_listing(user_id, ask_id):
    sql = "UPDATE asks SET buyer_user_id=%s, fulfilled=1 where ask_id=%s"

    try:
        with Database() as database:
            result = database.execute_insert_query(sql, (user_id, ask_id))

        return result
    except Exception as e:
        raise DatabaseException(e)


