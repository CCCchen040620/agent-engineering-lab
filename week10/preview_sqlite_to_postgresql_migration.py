import psycopg

from backend.config import DATABASE_URL, SQLITE_ADMIN_DATABASE_PATH
from backend.services.database_url_service import is_postgresql_database
from backend.services.postgresql_document_repository import (
    list_all_chunks_from_postgresql,
    list_documents_from_postgresql,
)
from backend.services.postgresql_schema_service import (
    initialize_postgresql_knowledge_schema,
)
from backend.services.sqlite_document_repository import (
    create_connection as create_sqlite_connection,
    create_chunks_table,
    create_documents_table,
    list_chunks_with_documents,
    list_documents_from_db,
)


class SqliteMigrationPreviewRepository:
    def __init__(self, connection):
        self.connection = connection

    def list_documents(self):
        return list_documents_from_db(self.connection)

    def list_all_chunks(self):
        return list_chunks_with_documents(self.connection)


class PostgresqlMigrationPreviewRepository:
    def __init__(self, connection):
        self.connection = connection

    def list_documents(self):
        return list_documents_from_postgresql(self.connection)

    def list_all_chunks(self):
        return list_all_chunks_from_postgresql(self.connection)


def preview_sqlite_to_postgresql_migration(
    sqlite_repository,
    postgresql_repository,
) -> dict:
    sqlite_documents = sqlite_repository.list_documents()
    sqlite_chunks = sqlite_repository.list_all_chunks()

    postgresql_documents = postgresql_repository.list_documents()
    postgresql_chunks = postgresql_repository.list_all_chunks()

    postgresql_titles = set()

    for document in postgresql_documents:
        postgresql_titles.add(document["title"])

        sqlite_chunk_count_by_document_id = {}

    for chunk in sqlite_chunks:
        document_id = chunk["document_id"]
        sqlite_chunk_count_by_document_id[document_id] = (
            sqlite_chunk_count_by_document_id.get(document_id, 0) + 1
        )

    missing_document_titles = []
    document_previews = []
    pending_document_count = 0
    pending_chunk_count = 0

    for document in sqlite_documents:
        title = document["title"]
        sqlite_chunk_count = sqlite_chunk_count_by_document_id.get(document["id"], 0)
        exists_in_postgresql = title in postgresql_titles
        will_migrate = not exists_in_postgresql

        if will_migrate:
            missing_document_titles.append(title)
            pending_document_count = pending_document_count + 1
            pending_chunk_count = pending_chunk_count + sqlite_chunk_count

        document_previews.append(
            {
                "title": title,
                "sqlite_chunk_count": sqlite_chunk_count,
                "exists_in_postgresql": exists_in_postgresql,
                "will_migrate": will_migrate,
            }
        )

    sqlite_is_empty = len(sqlite_documents) == 0

    message = ""

    if sqlite_is_empty:
        message = "SQLite 中暂无可迁移文档。"

    return {
        "sqlite_document_count": len(sqlite_documents),
        "sqlite_chunk_count": len(sqlite_chunks),
        "postgresql_document_count": len(postgresql_documents),
        "postgresql_chunk_count": len(postgresql_chunks),
        "sqlite_is_empty": sqlite_is_empty,
        "message": message,
        "missing_document_titles": missing_document_titles,
        "pending_document_count": pending_document_count,
        "pending_chunk_count": pending_chunk_count,
        "pending_embedding_count": pending_chunk_count,
        "document_previews": document_previews,
    }


def print_migration_preview(preview: dict):
    print("SQLite -> PostgreSQL 迁移预览")
    print("SQLite 文档数量：", preview["sqlite_document_count"])
    print("SQLite chunks 数量：", preview["sqlite_chunk_count"])
    print("PostgreSQL 文档数量：", preview["postgresql_document_count"])
    print("PostgreSQL chunks 数量：", preview["postgresql_chunk_count"])
    print("预计迁移文档数量：", preview["pending_document_count"])
    print("预计迁移 chunks 数量：", preview["pending_chunk_count"])
    print("预计生成 embeddings 数量：", preview["pending_embedding_count"])
    print("-" * 50)

    if preview["sqlite_is_empty"]:
        print(preview["message"])
        return

    if len(preview["missing_document_titles"]) == 0:
        print("SQLite 中没有发现尚未出现在 PostgreSQL 的文档。")
    else:
        print("SQLite 中尚未出现在 PostgreSQL 的文档：")

        for title in preview["missing_document_titles"]:
            print("-", title)

    print("-" * 50)
    print("文档迁移明细：")

    for item in preview["document_previews"]:
        status = "待迁移" if item["will_migrate"] else "已存在，跳过"
        print(
            f"- {item['title']} | chunks: {item['sqlite_chunk_count']} | {status}"
        )


def main():
    if not is_postgresql_database(DATABASE_URL):
        print("DATABASE_URL 不是 PostgreSQL 地址，已停止。")
        print("当前 DATABASE_URL:", DATABASE_URL)
        return

    sqlite_connection = create_sqlite_connection(SQLITE_ADMIN_DATABASE_PATH)
    create_documents_table(sqlite_connection)
    create_chunks_table(sqlite_connection)

    try:
        sqlite_repository = SqliteMigrationPreviewRepository(sqlite_connection)

        with psycopg.connect(DATABASE_URL) as connection:
            initialize_postgresql_knowledge_schema(connection)
            postgresql_repository = PostgresqlMigrationPreviewRepository(connection)

            preview = preview_sqlite_to_postgresql_migration(
                sqlite_repository=sqlite_repository,
                postgresql_repository=postgresql_repository,
            )

        print_migration_preview(preview)
    finally:
        sqlite_connection.close()


if __name__ == "__main__":
    main()
