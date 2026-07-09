import sqlite3

from backend.services.sqlite_conversation_repository import (
    create_conversations_table,
    create_messages_table,
)
from week04.settings import SQLITE_DATABASE_PATH


def column_exists(
    connection: sqlite3.Connection,
    table_name: str,
    column_name: str,
) -> bool:
    cursor = connection.execute(f"PRAGMA table_info({table_name})")
    rows = cursor.fetchall()

    for row in rows:
        if row[1] == column_name:
            return True

    return False


def migrate_messages_metadata_json(connection: sqlite3.Connection) -> None:
    if column_exists(connection, "messages", "metadata_json"):
        return

    connection.execute(
        """
        ALTER TABLE messages
        ADD COLUMN metadata_json TEXT NOT NULL DEFAULT '{}'
        """
    )

    connection.commit()


def migrate_conversation_schema(connection: sqlite3.Connection) -> None:
    create_conversations_table(connection)
    create_messages_table(connection)
    migrate_messages_metadata_json(connection)


def main() -> None:
    connection = sqlite3.connect(SQLITE_DATABASE_PATH)

    migrate_conversation_schema(connection)

    connection.close()

    print("SQLite schema migration completed.")


if __name__ == "__main__":
    main()