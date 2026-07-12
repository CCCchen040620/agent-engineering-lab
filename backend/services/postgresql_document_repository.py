def row_to_document(row) -> dict:
    return {
        "id": row[0],
        "title": row[1],
        "file_type": row[2],
        "chunk_count": row[3],
        "is_indexed": bool(row[4]),
    }


def list_documents_from_postgresql(connection) -> list[dict]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, title, file_type, chunk_count, is_indexed
            FROM documents
            ORDER BY id
            """
        )

        rows = cursor.fetchall()

    documents = []

    for row in rows:
        documents.append(row_to_document(row))

    return documents


def insert_document_to_postgresql(
    connection,
    title: str,
    file_type: str,
    chunk_count: int,
    is_indexed: bool,
) -> dict:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO documents (title, file_type, chunk_count, is_indexed)
            VALUES (%s, %s, %s, %s)
            RETURNING id, title, file_type, chunk_count, is_indexed
            """,
            (title, file_type, chunk_count, is_indexed),
        )

        row = cursor.fetchone()

    connection.commit()

    return row_to_document(row)