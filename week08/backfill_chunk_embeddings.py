from backend.services.ollama_embedding_service import embed_with_ollama
from backend.services.sqlite_document_repository import (
    create_chunks_table,
    create_connection,
    create_documents_table,
    list_chunks_with_documents,
)
from backend.services.sqlite_embedding_repository import (
    create_chunk_embeddings_table,
    ensure_chunk_embedding,
    find_chunk_embedding_by_chunk_id,
)
from week04.settings import SQLITE_DATABASE_PATH


def backfill_chunk_embeddings(
    database_path: str = SQLITE_DATABASE_PATH,
) -> dict:
    """为历史 chunks 补齐缺失的 embeddings。"""
    connection = create_connection(database_path)

    create_documents_table(connection)
    create_chunks_table(connection)
    create_chunk_embeddings_table(connection)

    chunks = list_chunks_with_documents(connection)

    created_count = 0
    skipped_count = 0

    for chunk in chunks:
        existing_embedding = find_chunk_embedding_by_chunk_id(
            connection,
            chunk["chunk_id"],
        )

        if existing_embedding is not None:
            skipped_count = skipped_count + 1
            continue

        embedding = embed_with_ollama(chunk["text"])

        ensure_chunk_embedding(
            connection,
            chunk_id=chunk["chunk_id"],
            embedding=embedding,
        )

        created_count = created_count + 1

    connection.close()

    return {
        "total_chunks": len(chunks),
        "created": created_count,
        "skipped": skipped_count,
    }


def main():
    result = backfill_chunk_embeddings()

    print("总 chunks 数量：", result["total_chunks"])
    print("新增 embedding 数量：", result["created"])
    print("已存在跳过数量：", result["skipped"])


if __name__ == "__main__":
    main()