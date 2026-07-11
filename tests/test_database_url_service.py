import pytest

from backend.services.database_url_service import (
    is_postgresql_database,
    is_sqlite_database,
    parse_database_url,
)


def test_parse_sqlite_database_url():
    result = parse_database_url("sqlite:///data/app.db")

    assert result == {
        "scheme": "sqlite",
        "path": "data/app.db",
    }


def test_parse_postgresql_database_url():
    result = parse_database_url(
        "postgresql://agent_user:secret@localhost:5432/agent_db"
    )

    assert result == {
        "scheme": "postgresql",
        "username": "agent_user",
        "password": "secret",
        "host": "localhost",
        "port": 5432,
        "database": "agent_db",
    }


def test_parse_postgres_alias_database_url():
    result = parse_database_url("postgres://user:secret@db:5432/agent_db")

    assert result["scheme"] == "postgresql"
    assert result["host"] == "db"
    assert result["database"] == "agent_db"


def test_detect_database_type():
    assert is_sqlite_database("sqlite:///data/app.db") is True
    assert is_postgresql_database("sqlite:///data/app.db") is False

    assert is_sqlite_database("postgresql://user:secret@localhost:5432/app") is False
    assert is_postgresql_database("postgresql://user:secret@localhost:5432/app") is True


def test_parse_database_url_rejects_unknown_scheme():
    with pytest.raises(ValueError) as error:
        parse_database_url("mysql://user:secret@localhost/app")

    assert "Unsupported database scheme" in str(error.value)
