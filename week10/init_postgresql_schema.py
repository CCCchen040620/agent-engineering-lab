import psycopg

from backend.config import DATABASE_URL
from backend.services.database_url_service import is_postgresql_database
from backend.services.postgresql_schema_service import (
    initialize_postgresql_knowledge_schema,
)


def initialize_schema_from_database_url(database_url: str) -> dict:
    if not is_postgresql_database(database_url):
        raise ValueError("DATABASE_URL must be a PostgreSQL URL.")

    with psycopg.connect(database_url) as connection:
        return initialize_postgresql_knowledge_schema(connection)


def main() -> None:
    result = initialize_schema_from_database_url(DATABASE_URL)

    print("PostgreSQL knowledge schema initialized.")
    print(result)


if __name__ == "__main__":
    main()