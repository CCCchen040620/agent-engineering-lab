import psycopg

from backend.config import DATABASE_URL
from backend.services.database_url_service import is_postgresql_database
from backend.services.postgresql_document_repository import (
    summarize_documents_by_source_from_postgresql,
)
from backend.services.postgresql_schema_service import (
    initialize_postgresql_knowledge_schema,
)


def preview_postgresql_evaluation_cleanup(
    connection,
    source: str = "evaluation",
) -> dict:
    initialize_postgresql_knowledge_schema(connection)

    return summarize_documents_by_source_from_postgresql(
        connection,
        source=source,
    )


def print_cleanup_preview(preview: dict):
    print("PostgreSQL evaluation 清理预览")
    print("数据来源：", preview["source"])
    print("将影响文档数量：", preview["document_count"])
    print("将影响 chunks 数量：", preview["chunk_count"])
    print("将影响 embeddings 数量：", preview["embedding_count"])

    print("-" * 50)

    if len(preview["documents"]) == 0:
        print("当前没有 evaluation 文档需要清理。")
        return

    for document in preview["documents"]:
        print(f"- {document['id']} {document['title']}")


def main():
    if not is_postgresql_database(DATABASE_URL):
        print("DATABASE_URL 不是 PostgreSQL 地址，已停止。")
        print("当前 DATABASE_URL:", DATABASE_URL)
        return

    with psycopg.connect(DATABASE_URL) as connection:
        preview = preview_postgresql_evaluation_cleanup(connection)

    print_cleanup_preview(preview)
    print("-" * 50)
    print("本脚本只做预览，不会删除任何数据。")


if __name__ == "__main__":
    main()
