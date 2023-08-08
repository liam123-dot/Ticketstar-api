def calculate_event_searches(database, event_id, since, to):

    sql = """
    SELECT *
    FROM EventSearches
    WHERE event_id = %s AND time > %s AND time < %s;
    """

    results = database.execute_select_query(sql, (event_id, since, to))

    return len(results)

