import argparse

import psycopg

from backend.config import (
    DATABASE_URL,
    EMBEDDING_MODEL,
    SQLITE_ADMIN_DATABASE_PATH,
)
from backend.services.database_url_service import is_postgresql_database
from backend.services.ollama_embedding_service import embed_with_ollama
from backend.services.postgresql_schema_service import (
    initialize_postgresql_knowledge_schema,
)
from backend.services.sqlite_document_repository import (
    create_chunks_table,
    create_connection as create_sqlite_connection,
    create_documents_table,
)
from week10.migrate_one_sqlite_document_to_postgresql import (
    RealPostgresqlMigrationRepository,
    RealSqliteMigrationRepository,
    migrate_one_sqlite_document_to_postgresql,
)


def migrate_sqlite_documents_to_postgresql(
    sqlite_repository,
    postgresql_repository,
    embedder,
    embedding_model: str,
    source: str = "migration",
    confirm: bool = False,
) -> dict:
    if confirm is False:
        return {
            "confirmed": False,
            "blocked": True,
            "reason": "confirm_required",
            "total_sqlite_documents": 0,
            "created_document_count": 0,
            "skipped_document_count": 0,
            "migrated_chunk_count": 0,
            "embedding_count": 0,
            "source": source,
            "items": [],
        }
    sqlite_documents = sqlite_repository.list_documents()
    items = []

    for document in sqlite_documents:
        item = migrate_one_sqlite_document_to_postgresql(
            sqlite_repository=sqlite_repository,
            postgresql_repository=postgresql_repository,
            title=document["title"],
            embedder=embedder,
            embedding_model=embedding_model,
            source=source,
        )
        items.append(item)

    created_document_count = 0
    skipped_document_count = 0
    migrated_chunk_count = 0
    embedding_count = 0

    for item in items:
        if item["created"]:
            created_document_count = created_document_count + 1

        if item["skipped"]:
            skipped_document_count = skipped_document_count + 1

        migrated_chunk_count = migrated_chunk_count + item["chunk_count"]
        embedding_count = embedding_count + item["embedding_count"]

    return {
        "confirmed": True,
        "blocked": False,
        "reason": "",
        "total_sqlite_documents": len(sqlite_documents),
        "created_document_count": created_document_count,
        "skipped_document_count": skipped_document_count,
        "migrated_chunk_count": migrated_chunk_count,
        "embedding_count": embedding_count,
        "source": source,
        "items": items,
    }


def print_batch_migration_result(result: dict):
    if result["blocked"]:
        print("未确认执行批量迁移，已停止。")
        print("如需执行，请使用 --confirm")
        return

    print("SQLite 批量迁移到 PostgreSQL 完成。")
    print("是否确认执行：", result["confirmed"])
    print("SQLite 文档总数：", result["total_sqlite_documents"])
    print("新建文档数量：", result["created_document_count"])
    print("跳过文档数量：", result["skipped_document_count"])
    print("迁移 chunks 数量：", result["migrated_chunk_count"])
    print("写入 embeddings 数量：", result["embedding_count"])
    print("source：", result["source"])

    for item in result["items"]:
        print("-" * 50)
        print("文档标题：", item["title"])
        print("是否创建：", item["created"])
        print("是否跳过：", item["skipped"])
        print("跳过原因：", item["reason"])
        print("迁移 chunks 数量：", item["chunk_count"])
        print("写入 embeddings 数量：", item["embedding_count"])


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", action="store_true")
    args = parser.parse_args(argv)

    if not is_postgresql_database(DATABASE_URL):
        print("DATABASE_URL 不是 PostgreSQL 地址，已停止。")
        print("当前 DATABASE_URL:", DATABASE_URL)
        return

    sqlite_connection = create_sqlite_connection(SQLITE_ADMIN_DATABASE_PATH)
    create_documents_table(sqlite_connection)
    create_chunks_table(sqlite_connection)

    try:
        sqlite_repository = RealSqliteMigrationRepository(sqlite_connection)

        with psycopg.connect(DATABASE_URL) as postgresql_connection:
            initialize_postgresql_knowledge_schema(postgresql_connection)

            postgresql_repository = RealPostgresqlMigrationRepository(
                postgresql_connection,
            )

            result = migrate_sqlite_documents_to_postgresql(
                sqlite_repository=sqlite_repository,
                postgresql_repository=postgresql_repository,
                embedder=embed_with_ollama,
                embedding_model=EMBEDDING_MODEL,
                confirm=args.confirm,
            )

        print_batch_migration_result(result)
    finally:
        sqlite_connection.close()


if __name__ == "__main__":
    main()