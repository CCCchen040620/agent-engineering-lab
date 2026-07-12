import psycopg

from backend.config import DATABASE_URL
from backend.services.database_url_service import is_postgresql_database
from backend.services.postgresql_document_repository import (
    insert_chunk_to_postgresql,
    insert_document_to_postgresql,
)
from backend.services.postgresql_embedding_repository import (
    insert_chunk_embedding_to_postgresql,
)
from backend.services.postgresql_schema_service import (
    initialize_postgresql_knowledge_schema,
)
from backend.services.postgresql_vector_search_repository import (
    search_chunks_by_vector_from_postgresql,
)


def build_fake_embedding(first_value: float, size: int = 1024) -> list[float]:
    embedding = [0.0] * size
    embedding[0] = first_value

    return embedding


def main() -> None:
    if not is_postgresql_database(DATABASE_URL):
        raise ValueError("DATABASE_URL must be a PostgreSQL URL.")

    with psycopg.connect(DATABASE_URL) as connection:
        initialize_postgresql_knowledge_schema(connection)

        document = insert_document_to_postgresql(
            connection,
            title="PostgreSQL 向量检索测试文档",
            file_type="md",
            chunk_count=2,
            is_indexed=True,
        )

        first_chunk = insert_chunk_to_postgresql(
            connection,
            document_id=document["id"],
            text="员工每天需要完成 8 小时工作。",
            chunk_index=0,
        )

        second_chunk = insert_chunk_to_postgresql(
            connection,
            document_id=document["id"],
            text="差旅报销需要在出差结束后 7 天内提交。",
            chunk_index=1,
        )

        insert_chunk_embedding_to_postgresql(
            connection,
            chunk_id=first_chunk["id"],
            embedding=build_fake_embedding(1.0),
            model="fake-embedding-1024",
        )

        insert_chunk_embedding_to_postgresql(
            connection,
            chunk_id=second_chunk["id"],
            embedding=build_fake_embedding(0.2),
            model="fake-embedding-1024",
        )

        results = search_chunks_by_vector_from_postgresql(
            connection,
            query_embedding=build_fake_embedding(1.0),
            top_k=2,
        )

    print("PostgreSQL 向量检索结果：")

    for index, item in enumerate(results, start=1):
        print(f"[{index}] {item['document_title']}")
        print("片段：", item["text"])
        print("距离：", item["distance"])
        print("分数：", item["score"])
        print("-" * 40)


if __name__ == "__main__":
    main()