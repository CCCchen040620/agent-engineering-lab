from backend.services.sqlite_document_repository import (
    create_chunks_table,
    create_connection,
    create_documents_table,
    insert_chunk_to_db,
    insert_document_to_db,
)
from backend.services.sqlite_embedding_repository import (
    create_chunk_embeddings_table,
    find_chunk_embedding_by_chunk_id,
    insert_chunk_embedding_to_db,
    list_chunk_embeddings_from_db,
    ensure_chunk_embedding,
)


def test_insert_chunk_embedding_to_db(tmp_path):
    database_path = tmp_path / "test.db"
    connection = create_connection(str(database_path))

    create_documents_table(connection)
    create_chunks_table(connection)
    create_chunk_embeddings_table(connection)

    document = insert_document_to_db(
        connection,
        title="远程办公制度",
        file_type="md",
        chunk_count=1,
        is_indexed=True,
    )
    chunk = insert_chunk_to_db(
        connection,
        document_id=document["id"],
        text="员工可以远程办公。",
    )

    chunk_embedding = insert_chunk_embedding_to_db(
        connection,
        chunk_id=chunk["id"],
        embedding=[0.1, 0.2, 0.3],
    )

    connection.close()

    assert chunk_embedding["id"] == 1
    assert chunk_embedding["chunk_id"] == chunk["id"]
    assert chunk_embedding["embedding"] == [0.1, 0.2, 0.3]


def test_find_chunk_embedding_by_chunk_id(tmp_path):
    database_path = tmp_path / "test.db"
    connection = create_connection(str(database_path))

    create_documents_table(connection)
    create_chunks_table(connection)
    create_chunk_embeddings_table(connection)

    document = insert_document_to_db(
        connection,
        title="远程办公制度",
        file_type="md",
        chunk_count=1,
        is_indexed=True,
    )
    chunk = insert_chunk_to_db(
        connection,
        document_id=document["id"],
        text="员工可以远程办公。",
    )

    insert_chunk_embedding_to_db(
        connection,
        chunk_id=chunk["id"],
        embedding=[0.1, 0.2, 0.3],
    )

    chunk_embedding = find_chunk_embedding_by_chunk_id(connection, chunk["id"])

    connection.close()

    assert chunk_embedding["chunk_id"] == chunk["id"]
    assert chunk_embedding["embedding"] == [0.1, 0.2, 0.3]


def test_list_chunk_embeddings_from_db(tmp_path):
    database_path = tmp_path / "test.db"
    connection = create_connection(str(database_path))

    create_documents_table(connection)
    create_chunks_table(connection)
    create_chunk_embeddings_table(connection)

    document = insert_document_to_db(
        connection,
        title="远程办公制度",
        file_type="md",
        chunk_count=1,
        is_indexed=True,
    )
    chunk = insert_chunk_to_db(
        connection,
        document_id=document["id"],
        text="员工可以远程办公。",
    )

    insert_chunk_embedding_to_db(
        connection,
        chunk_id=chunk["id"],
        embedding=[0.1, 0.2, 0.3],
    )

    embeddings = list_chunk_embeddings_from_db(connection)

    connection.close()

    assert len(embeddings) == 1
    assert embeddings[0]["embedding"] == [0.1, 0.2, 0.3]


def test_ensure_chunk_embedding_returns_existing_embedding(tmp_path):
    database_path = tmp_path / "test.db"
    connection = create_connection(str(database_path))

    create_documents_table(connection)
    create_chunks_table(connection)
    create_chunk_embeddings_table(connection)

    document = insert_document_to_db(
        connection,
        title="远程办公制度",
        file_type="md",
        chunk_count=1,
        is_indexed=True,
    )
    chunk = insert_chunk_to_db(
        connection,
        document_id=document["id"],
        text="员工可以远程办公。",
    )

    first_embedding = ensure_chunk_embedding(
        connection,
        chunk_id=chunk["id"],
        embedding=[0.1, 0.2, 0.3],
    )
    second_embedding = ensure_chunk_embedding(
        connection,
        chunk_id=chunk["id"],
        embedding=[9.9, 9.9, 9.9],
    )

    connection.close()

    assert first_embedding["id"] == second_embedding["id"]
    assert second_embedding["embedding"] == [0.1, 0.2, 0.3]