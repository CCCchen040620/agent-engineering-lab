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


def insert_document_to_db(
    connection,
    title: str,
    file_type: str,
    chunk_count: int,
    is_indexed: bool,
) -> dict:
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO documents (title, file_type, chunk_count, is_indexed)
        VALUES (?, ?, ?, ?)
        """,
        (title, file_type, chunk_count, int(is_indexed)),
    )

    connection.commit()

    document_id = cursor.lastrowid

    cursor.execute(
        """
        SELECT id, title, file_type, chunk_count, is_indexed
        FROM documents
        WHERE id = ?
        """,
        (document_id,),
    )

    row = cursor.fetchone()

    return row_to_document(row)


def try_insert_document_to_db(
    connection,
    title: str,
    file_type: str,
    chunk_count: int,
    is_indexed: bool,
) -> dict | None:
    try:
        return insert_document_to_db(
            connection,
            title=title,
            file_type=file_type,
            chunk_count=chunk_count,
            is_indexed=is_indexed,
        )
    except sqlite3.IntegrityError:
        return None


def list_documents_from_db_filtered(
    connection,
    indexed_only: bool = False,
    file_type: str | None = None,
) -> list[dict]:
    query = """
        SELECT id, title, file_type, chunk_count, is_indexed
        FROM documents
        WHERE 1 = 1
    """
    params = []

    if indexed_only:
        query = query + " AND is_indexed = ?"
        params.append(1)

    if file_type is not None:
        query = query + " AND file_type = ?"
        params.append(file_type)

    cursor = connection.cursor()
    cursor.execute(query, params)

    rows = cursor.fetchall()

    documents = []

    for row in rows:
        documents.append(row_to_document(row))

    return documents


def find_document_from_db_by_id(connection, document_id: int) -> dict | None:
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, title, file_type, chunk_count, is_indexed
        FROM documents
        WHERE id = ?
        """,
        (document_id,),
    )

    row = cursor.fetchone()

    if row is None:
        return None

    return row_to_document(row)