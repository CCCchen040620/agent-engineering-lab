def row_to_document(row) -> dict:
    return {
        "id": row[0],
        "title": row[1],
        "file_type": row[2],
        "chunk_count": row[3],
        "is_indexed": bool(row[4]),
    }


def row_to_chunk(row) -> dict:
    return {
        "id": row[0],
        "document_id": row[1],
        "text": row[2],
        "chunk_index": row[3],
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


def insert_chunk_to_postgresql(
    connection,
    document_id: int,
    text: str,
    chunk_index: int,
) -> dict:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO chunks (document_id, text, chunk_index)
            VALUES (%s, %s, %s)
            RETURNING id, document_id, text, chunk_index
            """,
            (document_id, text, chunk_index),
        )

        row = cursor.fetchone()

    connection.commit()

    return row_to_chunk(row)


def list_chunks_by_document_from_postgresql(
    connection,
    document_id: int,
) -> list[dict]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, document_id, text, chunk_index
            FROM chunks
            WHERE document_id = %s
            ORDER BY chunk_index, id
            """,
            (document_id,),
        )

        rows = cursor.fetchall()

    chunks = []

    for row in rows:
        chunks.append(row_to_chunk(row))

    return chunks