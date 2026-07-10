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


def migrate_messages_metadata_json(connection: sqlite3.Connection) -> bool:
    if column_exists(connection, "messages", "metadata_json"):
        return False

    connection.execute(
        """
        ALTER TABLE messages
        ADD COLUMN metadata_json TEXT NOT NULL DEFAULT '{}'
        """
    )

    connection.commit()

    return True


def migrate_conversation_schema(connection: sqlite3.Connection) -> dict:
    create_conversations_table(connection)
    create_messages_table(connection)

    summary_added = migrate_conversation_summary(connection)
    metadata_json_added = migrate_messages_metadata_json(connection)

    return {
        "conversations_table_ready": True,
        "messages_table_ready": True,
        "summary_added": summary_added,
        "metadata_json_added": metadata_json_added,
    }


def migrate_conversation_summary(connection: sqlite3.Connection) -> bool:
    if column_exists(connection, "conversations", "summary"):
        return False

    connection.execute(
        """
        ALTER TABLE conversations
        ADD COLUMN summary TEXT NOT NULL DEFAULT ''
        """
    )

    connection.commit()

    return True


def main() -> None:
    connection = sqlite3.connect(SQLITE_DATABASE_PATH)

    result = migrate_conversation_schema(connection)

    connection.close()

    print("SQLite schema migration completed.")
    print(result)


if __name__ == "__main__":
    main()