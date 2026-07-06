import json


def create_chunk_embeddings_table(connection) -> None:
    """创建保存 chunk embedding 的 SQLite 表。"""
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS chunk_embeddings (
            id INTEGER PRIMARY KEY,
            chunk_id INTEGER NOT NULL UNIQUE,
            embedding_json TEXT NOT NULL,
            FOREIGN KEY (chunk_id) REFERENCES chunks (id)
        )
        """
    )

    connection.commit()


def row_to_chunk_embedding(row) -> dict:
    return {
        "id": row[0],
        "chunk_id": row[1],
        "embedding": json.loads(row[2]),
    }


def insert_chunk_embedding_to_db(
    connection,
    chunk_id: int,
    embedding: list[float],
) -> dict:
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO chunk_embeddings (chunk_id, embedding_json)
        VALUES (?, ?)
        """,
        (chunk_id, json.dumps(embedding)),
    )

    connection.commit()

    embedding_id = cursor.lastrowid

    cursor.execute(
        """
        SELECT id, chunk_id, embedding_json
        FROM chunk_embeddings
        WHERE id = ?
        """,
        (embedding_id,),
    )

    row = cursor.fetchone()

    return row_to_chunk_embedding(row)


def find_chunk_embedding_by_chunk_id(connection, chunk_id: int) -> dict | None:
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, chunk_id, embedding_json
        FROM chunk_embeddings
        WHERE chunk_id = ?
        """,
        (chunk_id,),
    )

    row = cursor.fetchone()

    if row is None:
        return None

    return row_to_chunk_embedding(row)


def list_chunk_embeddings_from_db(connection) -> list[dict]:
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, chunk_id, embedding_json
        FROM chunk_embeddings
        """
    )

    rows = cursor.fetchall()

    embeddings = []

    for row in rows:
        embeddings.append(row_to_chunk_embedding(row))

    return embeddings


def ensure_chunk_embedding(
    connection,
    chunk_id: int,
    embedding: list[float],
) -> dict:
    existing_embedding = find_chunk_embedding_by_chunk_id(connection, chunk_id)

    if existing_embedding is not None:
        return existing_embedding

    return insert_chunk_embedding_to_db(
        connection,
        chunk_id=chunk_id,
        embedding=embedding,
    )


def summarize_document_embedding_status(connection) -> list[dict]:
    """统计每份文档的 chunks 是否已经完成 embedding 索引。"""
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            documents.id,
            documents.title,
            documents.chunk_count,
            COUNT(chunk_embeddings.id) AS embedding_count
        FROM documents
        LEFT JOIN chunks ON chunks.document_id = documents.id
        LEFT JOIN chunk_embeddings ON chunk_embeddings.chunk_id = chunks.id
        GROUP BY documents.id, documents.title, documents.chunk_count
        """
    )

    rows = cursor.fetchall()

    results = []

    for row in rows:
        chunk_count = row[2]
        embedding_count = row[3]

        results.append(
            {
                "document_id": row[0],
                "title": row[1],
                "chunk_count": chunk_count,
                "embedding_count": embedding_count,
                "is_embedding_complete": chunk_count == embedding_count,
            }
        )

    return results


def list_chunks_with_embeddings(connection) -> list[dict]:
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            chunks.id,
            chunks.document_id,
            documents.title,
            chunks.text,
            chunk_embeddings.embedding_json
        FROM chunks
        JOIN documents ON chunks.document_id = documents.id
        JOIN chunk_embeddings ON chunk_embeddings.chunk_id = chunks.id
        """
    )

    rows = cursor.fetchall()

    results = []

    for row in rows:
        results.append(
            {
                "chunk_id": row[0],
                "document_id": row[1],
                "document_title": row[2],
                "text": row[3],
                "embedding_json": row[4],
            }
        )

    return results