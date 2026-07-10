import json
import sqlite3


def create_conversations_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            summary TEXT NOT NULL DEFAULT ''
        )
        """
    )

    connection.commit()


def create_messages_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY,
            conversation_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            metadata_json TEXT NOT NULL DEFAULT '{}',
            FOREIGN KEY (conversation_id) REFERENCES conversations(id)
        )
        """
    )

    connection.commit()

    
def create_conversation(
    connection: sqlite3.Connection,
    title: str,
) -> dict:
    cursor = connection.execute(
        """
        INSERT INTO conversations (title)
        VALUES (?)
        """,
        (title,),
    )

    connection.commit()

    conversation_id = cursor.lastrowid

    return {
        "id": conversation_id,
        "title": title,
        "summary": "",
    }


def list_conversations(connection: sqlite3.Connection) -> list[dict]:
    cursor = connection.execute(
        """
        SELECT id, title, summary
        FROM conversations
        ORDER BY id
        """
    )

    rows = cursor.fetchall()

    conversations = []

    for row in rows:
        conversations.append(
            {
                "id": row[0],
                "title": row[1],
                "summary": row[2],
            }
        )

    return conversations


def find_conversation_by_id(
    connection: sqlite3.Connection,
    conversation_id: int,
) -> dict | None:
    cursor = connection.execute(
        """
        SELECT id, title, summary
        FROM conversations
        WHERE id = ?
        """,
        (conversation_id,),
    )

    row = cursor.fetchone()

    if row is None:
        return None

    return {
        "id": row[0],
        "title": row[1],
        "summary": row[2],
    }

    
def add_message(
    connection: sqlite3.Connection,
    conversation_id: int,
    role: str,
    content: str,
    metadata: dict | None = None,
) -> dict:
    if metadata is None:
        metadata = {}

    metadata_json = json.dumps(metadata, ensure_ascii=False)

    cursor = connection.execute(
        """
        INSERT INTO messages (conversation_id, role, content, metadata_json)
        VALUES (?, ?, ?, ?)
        """,
        (conversation_id, role, content, metadata_json),
    )

    connection.commit()

    message_id = cursor.lastrowid

    return {
        "id": message_id,
        "conversation_id": conversation_id,
        "role": role,
        "content": content,
        "metadata": metadata,
    }


def list_messages_by_conversation(
    connection: sqlite3.Connection,
    conversation_id: int,
) -> list[dict]:
    cursor = connection.execute(
        """
        SELECT id, conversation_id, role, content, metadata_json
        FROM messages
        WHERE conversation_id = ?
        ORDER BY id
        """,
        (conversation_id,),
    )

    rows = cursor.fetchall()

    messages = []

    for row in rows:
        metadata = json.loads(row[4])

        messages.append(
            {
                "id": row[0],
                "conversation_id": row[1],
                "role": row[2],
                "content": row[3],
                "metadata": metadata,
            }
        )

    return messages


def update_conversation_summary(
    connection: sqlite3.Connection,
    conversation_id: int,
    summary: str,
) -> dict | None:
    cursor = connection.execute(
        """
        UPDATE conversations
        SET summary = ?
        WHERE id = ?
        """,
        (summary, conversation_id),
    )

    connection.commit()

    if cursor.rowcount == 0:
        return None

    return find_conversation_by_id(connection, conversation_id)