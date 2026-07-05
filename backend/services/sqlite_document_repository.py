import sqlite3


def create_connection(database_path: str):
    return sqlite3.connect(database_path)


def create_documents_table(connection) -> None:
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL UNIQUE,
            file_type TEXT NOT NULL,
            chunk_count INTEGER NOT NULL,
            is_indexed INTEGER NOT NULL
        )
        """
    )

    connection.commit()


def row_to_document(row) -> dict:
    return {
        "id": row[0],
        "title": row[1],
        "file_type": row[2],
        "chunk_count": row[3],
        "is_indexed": bool(row[4]),
    }


def list_documents_from_db(connection) -> list[dict]:
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, title, file_type, chunk_count, is_indexed
        FROM documents
        """
    )

    rows = cursor.fetchall()

    documents = []

    for row in rows:
        documents.append(row_to_document(row))

    return documents