import sqlite3

import pytest

from backend.services.database_connection_service import create_database_connection


def test_create_database_connection_with_sqlite_url(tmp_path):
    database_path = tmp_path / "test.db"
    database_url = f"sqlite:///{database_path}"

    connection = create_database_connection(database_url)

    assert isinstance(connection, sqlite3.Connection)

    connection.close()


def test_create_database_connection_rejects_unsupported_database():
    with pytest.raises(ValueError):
        create_database_connection("mysql://user:password@localhost/app")