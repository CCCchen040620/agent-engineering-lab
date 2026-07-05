import sqlite3


def create_connection(database_path: str):
    connection = sqlite3.connect(database_path)
    return connection


def create_documents_table(connection):
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


def insert_document(connection, title, file_type, chunk_count, is_indexed):
    existing_document = find_document_by_title(connection, title)

    if existing_document is not None:
        return None

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO documents (title, file_type, chunk_count, is_indexed)
        VALUES (?, ?, ?, ?)
        """,
        (title, file_type, chunk_count, int(is_indexed)),
    )

    connection.commit()

    return find_document_by_title(connection, title)


def list_documents(connection):
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
        document = {
            "id": row[0],
            "title": row[1],
            "file_type": row[2],
            "chunk_count": row[3],
            "is_indexed": bool(row[4]),
        }
        documents.append(document)

    return documents


def find_document_by_title(connection, title):
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, title, file_type, chunk_count, is_indexed
        FROM documents
        WHERE title = ?
        """,
        (title,),
    )

    row = cursor.fetchone()

    if row is None:
        return None

    return {
        "id": row[0],
        "title": row[1],
        "file_type": row[2],
        "chunk_count": row[3],
        "is_indexed": bool(row[4]),
    }


def main():
    connection = create_connection("data/app.db")

    create_documents_table(connection)

    insert_document(
        connection,
        title="员工手册",
        file_type="md",
        chunk_count=12,
        is_indexed=True,
    )

    documents = list_documents(connection)

    for document in documents:
        print(document)

    connection.close()


if __name__ == "__main__":
    main()