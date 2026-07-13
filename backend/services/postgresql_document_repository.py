def row_to_document(row) -> dict:
    return {
        "id": row[0],
        "title": row[1],
        "file_type": row[2],
        "chunk_count": row[3],
        "is_indexed": bool(row[4]),
        "source": row[5] if len(row) > 5 else "production",
    }


def row_to_chunk(row) -> dict:
    return {
        "id": row[0],
        "document_id": row[1],
        "text": row[2],
        "chunk_index": row[3],
    }


def list_documents_from_postgresql(
    connection,
    source: str | None = None,
) -> list[dict]:
    with connection.cursor() as cursor:
        if source is None:
            cursor.execute(
                """
                SELECT id, title, file_type, chunk_count, is_indexed, source
                FROM documents
                ORDER BY id
                """
            )
        else:
            cursor.execute(
                """
                SELECT id, title, file_type, chunk_count, is_indexed, source
                FROM documents
                WHERE source = %s
                ORDER BY id
                """,
                (source,),
            )

        rows = cursor.fetchall()

    documents = []

    for row in rows:
        documents.append(row_to_document(row))

    return documents


def find_document_by_title_from_postgresql(
    connection,
    title: str,
) -> dict | None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, title, file_type, chunk_count, is_indexed, source
            FROM documents
            WHERE title = %s
            """,
            (title,),
        )

        row = cursor.fetchone()

    if row is None:
        return None

    return row_to_document(row)


def update_document_source_by_title_from_postgresql(
    connection,
    title: str,
    source: str,
) -> dict | None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE documents
            SET source = %s
            WHERE title = %s
            RETURNING id, title, file_type, chunk_count, is_indexed, source
            """,
            (source, title),
        )

        row = cursor.fetchone()

    connection.commit()

    if row is None:
        return None

    return row_to_document(row)

    
def insert_document_to_postgresql(
    connection,
    title: str,
    file_type: str,
    chunk_count: int,
    is_indexed: bool,
    source: str = "production",
) -> dict:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO documents (title, file_type, chunk_count, is_indexed, source)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, title, file_type, chunk_count, is_indexed, source
            """,
            (title, file_type, chunk_count, is_indexed, source),
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


def list_all_chunks_from_postgresql(connection) -> list[dict]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, document_id, text, chunk_index
            FROM chunks
            ORDER BY id
            """
        )

        rows = cursor.fetchall()

    chunks = []

    for row in rows:
        chunks.append(row_to_chunk(row))

    return chunks


def delete_documents_by_source_from_postgresql(
    connection,
    source: str,
) -> int:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            DELETE FROM documents
            WHERE source = %s
            RETURNING id
            """,
            (source,),
        )

        rows = cursor.fetchall()

    connection.commit()

    return len(rows)


def summarize_documents_by_source_from_postgresql(
    connection,
    source: str,
) -> dict:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                documents.id,
                documents.title,
                COUNT(DISTINCT chunks.id) AS chunk_count,
                COUNT(DISTINCT chunk_embeddings.id) AS embedding_count
            FROM documents
            LEFT JOIN chunks
                ON chunks.document_id = documents.id
            LEFT JOIN chunk_embeddings
                ON chunk_embeddings.chunk_id = chunks.id
            WHERE documents.source = %s
            GROUP BY documents.id, documents.title
            ORDER BY documents.id
            """,
            (source,),
        )

        rows = cursor.fetchall()

    documents = []
    chunk_count = 0
    embedding_count = 0

    for row in rows:
        documents.append(
            {
                "id": row[0],
                "title": row[1],
            }
        )
        chunk_count += row[2]
        embedding_count += row[3]

    return {
        "source": source,
        "document_count": len(documents),
        "chunk_count": chunk_count,
        "embedding_count": embedding_count,
        "documents": documents,
    }