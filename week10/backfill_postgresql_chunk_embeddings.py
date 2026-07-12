import psycopg

from backend.config import DATABASE_URL, EMBEDDING_MODEL
from backend.services.database_url_service import is_postgresql_database
from backend.services.ollama_embedding_service import embed_with_ollama
from backend.services.postgresql_document_repository import (
    list_all_chunks_from_postgresql,
)
from backend.services.postgresql_embedding_repository import (
    upsert_chunk_embedding_to_postgresql,
)
from backend.services.postgresql_schema_service import (
    initialize_postgresql_knowledge_schema,
)


def backfill_postgresql_chunk_embeddings(
    connection,
    model: str = EMBEDDING_MODEL,
) -> dict:
    initialize_postgresql_knowledge_schema(connection)

    chunks = list_all_chunks_from_postgresql(connection)

    updated_embeddings = 0

    for chunk in chunks:
        embedding = embed_with_ollama(chunk["text"], model=model)

        upsert_chunk_embedding_to_postgresql(
            connection,
            chunk_id=chunk["id"],
            embedding=embedding,
            model=model,
        )

        updated_embeddings = updated_embeddings + 1

    return {
        "total_chunks": len(chunks),
        "updated_embeddings": updated_embeddings,
        "model": model,
    }


def main():
    if not is_postgresql_database(DATABASE_URL):
        print("DATABASE_URL 不是 PostgreSQL 地址，已停止。")
        print("当前 DATABASE_URL:", DATABASE_URL)
        return

    with psycopg.connect(DATABASE_URL) as connection:
        result = backfill_postgresql_chunk_embeddings(connection)

    print("PostgreSQL chunk embedding 回填完成。")
    print("总 chunks 数量：", result["total_chunks"])
    print("更新 embedding 数量：", result["updated_embeddings"])
    print("模型：", result["model"])


if __name__ == "__main__":
    main()