from backend.config import DATABASE_URL
from backend.services.database_url_service import (
    get_sqlite_path_from_database_url,
    is_sqlite_database,
)
from backend.services.sqlite_document_repository import create_connection


def create_database_connection(database_url: str = DATABASE_URL):
    if is_sqlite_database(database_url):
        database_path = get_sqlite_path_from_database_url(database_url)
        return create_connection(database_path)

    raise ValueError("Unsupported database type.")