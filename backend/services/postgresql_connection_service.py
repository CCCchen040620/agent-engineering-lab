import psycopg


def check_postgresql_connection(database_url: str) -> dict:
    try:
        with psycopg.connect(database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()

        return {
            "status": "ok",
            "database_url": database_url,
        }
    except Exception as error:
        return {
            "status": "error",
            "database_url": database_url,
            "message": str(error),
        }