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


def test_create_database_connection_explains_postgresql_is_not_implemented():
    with pytest.raises(ValueError) as error:
        create_database_connection("postgresql://agent:secret@localhost:5432/agent_db")

    assert "PostgreSQL connection is not implemented yet" in str(error.value)