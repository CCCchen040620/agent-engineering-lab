import psycopg

from backend.config import DATABASE_URL
from backend.services.database_url_service import is_postgresql_database
from backend.services.postgresql_document_repository import (
    insert_chunk_to_postgresql,
    insert_document_to_postgresql,
    list_chunks_by_document_from_postgresql,
)
from backend.services.postgresql_embedding_repository import (
    find_chunk_embedding_by_chunk_id_from_postgresql,
    insert_chunk_embedding_to_postgresql,
)
from backend.services.postgresql_schema_service import (
    initialize_postgresql_knowledge_schema,
)


def build_fake_embedding(size: int = 1024) -> list[float]:
    embedding = []

    for index in range(size):
        embedding.append(index / size)

    return embedding


def main() -> None:
    if not is_postgresql_database(DATABASE_URL):
        raise ValueError("DATABASE_URL must be a PostgreSQL URL.")

    with psycopg.connect(DATABASE_URL) as connection:
        initialize_postgresql_knowledge_schema(connection)

        document = insert_document_to_postgresql(
            connection,
            title="PostgreSQL RAG 存储测试文档",
            file_type="md",
            chunk_count=1,
            is_indexed=True,
        )

        chunk = insert_chunk_to_postgresql(
            connection,
            document_id=document["id"],
            text="这是一条写入 PostgreSQL pgvector 的测试片段。",
            chunk_index=0,
        )

        embedding = insert_chunk_embedding_to_postgresql(
            connection,
            chunk_id=chunk["id"],
            embedding=build_fake_embedding(),
            model="fake-embedding-1024",
        )

        chunks = list_chunks_by_document_from_postgresql(
            connection,
            document_id=document["id"],
        )

        stored_embedding = find_chunk_embedding_by_chunk_id_from_postgresql(
            connection,
            chunk_id=chunk["id"],
        )

    print("新增文档：")
    print(document)

    print("新增片段：")
    print(chunk)

    print("新增 embedding：")
    print(
        {
            "id": embedding["id"],
            "chunk_id": embedding["chunk_id"],
            "embedding_size": len(embedding["embedding"]),
            "model": embedding["model"],
        }
    )

    print("该文档 chunk 数量：", len(chunks))
    print("查询到的 embedding 维度：", len(stored_embedding["embedding"]))


if __name__ == "__main__":
    main()