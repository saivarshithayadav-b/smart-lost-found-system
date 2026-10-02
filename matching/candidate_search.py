from database import get_db_connection


def get_found_candidates(
    exclude_user_id=None
):
    """
    Retrieve found-item records from the database.

    If exclude_user_id is provided,
    found items uploaded by that user are excluded.

    Returns:
        List of found items as dictionaries.
    """

    connection = None
    cursor = None

    try:
        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        if exclude_user_id is not None:

            cursor.execute(
                """
                SELECT *
                FROM found_items
                WHERE user_id != %s
                   OR user_id IS NULL
                ORDER BY created_at DESC
                """,
                (exclude_user_id,)
            )

        else:

            cursor.execute(
                """
                SELECT *
                FROM found_items
                ORDER BY created_at DESC
                """
            )

        candidates = cursor.fetchall()

        return candidates

    except Exception as error:
        print(
            "CANDIDATE SEARCH ERROR:",
            error
        )

        return []

    finally:

        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()