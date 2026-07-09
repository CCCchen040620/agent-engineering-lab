import sqlite3

from week10.migrate_sqlite_schema import (
    column_exists,
    migrate_conversation_schema,
    migrate_messages_metadata_json,
)


def test_column_exists_returns_true_when_column_exists():
    connection = sqlite3.connect(":memory:")

    connection.execute(
        """
        CREATE TABLE messages (
            id INTEGER PRIMARY KEY,
            metadata_json TEXT NOT NULL DEFAULT '{}'
        )
        """
    )

    result = column_exists(connection, "messages", "metadata_json")

    assert result is True

    connection.close()


def test_column_exists_returns_false_when_column_does_not_exist():
    connection = sqlite3.connect(":memory:")

    connection.execute(
        """
        CREATE TABLE messages (
            id INTEGER PRIMARY KEY,
            content TEXT NOT NULL
        )
        """
    )

    result = column_exists(connection, "messages", "metadata_json")

    assert result is False

    connection.close()


def test_migrate_messages_metadata_json_adds_missing_column():
    connection = sqlite3.connect(":memory:")

    connection.execute(
        """
        CREATE TABLE messages (
            id INTEGER PRIMARY KEY,
            content TEXT NOT NULL
        )
        """
    )

    migrate_messages_metadata_json(connection)

    assert column_exists(connection, "messages", "metadata_json") is True

    connection.close()


def test_migrate_messages_metadata_json_can_run_twice():
    connection = sqlite3.connect(":memory:")

    connection.execute(
        """
        CREATE TABLE messages (
            id INTEGER PRIMARY KEY,
            content TEXT NOT NULL
        )
        """
    )

    migrate_messages_metadata_json(connection)
    migrate_messages_metadata_json(connection)

    assert column_exists(connection, "messages", "metadata_json") is True

    connection.close()


def test_migrate_conversation_schema_creates_missing_tables():
    connection = sqlite3.connect(":memory:")

    migrate_conversation_schema(connection)

    assert column_exists(connection, "messages", "metadata_json") is True

    conversations_table = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name = 'conversations'
        """
    ).fetchone()

    messages_table = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name = 'messages'
        """
    ).fetchone()

    assert conversations_table is not None
    assert messages_table is not None

    connection.close()