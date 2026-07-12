import psycopg

from backend.config import DATABASE_URL
from backend.services.database_url_service import is_postgresql_database
from backend.services.postgresql_document_repository import (
    insert_document_to_postgresql,
    list_documents_from_postgresql,
)
from backend.services.postgresql_schema_service import (
    initialize_postgresql_knowledge_schema,
)


def main() -> None:
    if not is_postgresql_database(DATABASE_URL):
        raise ValueError("DATABASE_URL must be a PostgreSQL URL.")

    with psycopg.connect(DATABASE_URL) as connection:
        initialize_postgresql_knowledge_schema(connection)

        document = insert_document_to_postgresql(
            connection,
            title="PostgreSQL 测试文档",
            file_type="md",
            chunk_count=0,
            is_indexed=False,
        )

        documents = list_documents_from_postgresql(connection)

    print("新增文档：")
    print(document)

    print("当前 PostgreSQL 文档数量：", len(documents))

    for item in documents:
        print("-", item["id"], item["title"], item["file_type"], item["is_indexed"])


if __name__ == "__main__":
    main()