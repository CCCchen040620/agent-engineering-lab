import psycopg

from backend.config import (
    DATABASE_URL,
    EMBEDDING_MODEL,
    SQLITE_ADMIN_DATABASE_PATH,
)
from backend.services.database_url_service import is_postgresql_database
from backend.services.ollama_embedding_service import embed_with_ollama
from backend.services.postgresql_document_repository import (
    find_document_by_title_from_postgresql,
    insert_chunk_to_postgresql,
    insert_document_to_postgresql,
)
from backend.services.postgresql_embedding_repository import (
    upsert_chunk_embedding_to_postgresql,
)
from backend.services.postgresql_schema_service import (
    initialize_postgresql_knowledge_schema,
)
from backend.services.sqlite_document_repository import (
    create_chunks_table,
    create_connection as create_sqlite_connection,
    create_documents_table,
    find_document_from_db_by_title,
    list_chunks_by_document_id,
    list_documents_from_db,
)
from week10.seed_sqlite_migration_sample import SQLITE_MIGRATION_SAMPLE_TITLE


class RealSqliteMigrationRepository:
    def __init__(self, connection):
        self.connection = connection

    def list_documents(self):
        return list_documents_from_db(self.connection)

    def find_document_by_title(self, title: str):
        return find_document_from_db_by_title(self.connection, title)

    def list_chunks_by_document_id(self, document_id: int):
        return list_chunks_by_document_id(self.connection, document_id)


class RealPostgresqlMigrationRepository:
    def __init__(self, connection):
        self.connection = connection

    def find_document_by_title(self, title: str):
        return find_document_by_title_from_postgresql(self.connection, title)

    def insert_document(self, title, file_type, chunk_count, is_indexed, source):
        return insert_document_to_postgresql(
            self.connection,
            title=title,
            file_type=file_type,
            chunk_count=chunk_count,
            is_indexed=is_indexed,
            source=source,
        )

    def insert_chunk(self, document_id: int, text: str, chunk_index: int):
        return insert_chunk_to_postgresql(
            self.connection,
            document_id=document_id,
            text=text,
            chunk_index=chunk_index,
        )

    def upsert_embedding(self, chunk_id: int, embedding: list[float], model: str):
        return upsert_chunk_embedding_to_postgresql(
            self.connection,
            chunk_id=chunk_id,
            embedding=embedding,
            model=model,
        )


def print_migration_result(result: dict):
    print("SQLite 单文档迁移到 PostgreSQL 完成。")
    print("文档标题：", result["title"])
    print("是否创建：", result["created"])
    print("是否跳过：", result["skipped"])
    print("跳过原因：", result["reason"])
    print("迁移 chunks 数量：", result["chunk_count"])
    print("写入 embeddings 数量：", result["embedding_count"])
    print("source：", result["source"])


def migrate_one_sqlite_document_to_postgresql(
    sqlite_repository,
    postgresql_repository,
    title: str,
    embedder,
    embedding_model: str,
    source: str = "migration",
) -> dict:
    sqlite_document = sqlite_repository.find_document_by_title(title)

    if sqlite_document is None:
        return {
            "created": False,
            "skipped": True,
            "reason": "sqlite_document_not_found",
            "title": title,
            "chunk_count": 0,
            "embedding_count": 0,
            "source": source,
        }

    existing_postgresql_document = postgresql_repository.find_document_by_title(title)

    if existing_postgresql_document is not None:
        return {
            "created": False,
            "skipped": True,
            "reason": "postgresql_document_already_exists",
            "title": title,
            "chunk_count": 0,
            "embedding_count": 0,
            "source": source,
        }

    sqlite_chunks = sqlite_repository.list_chunks_by_document_id(
        sqlite_document["id"]
    )

    postgresql_document = postgresql_repository.insert_document(
        title=sqlite_document["title"],
        file_type=sqlite_document["file_type"],
        chunk_count=len(sqlite_chunks),
        is_indexed=True,
        source=source,
    )

    embedding_count = 0

    for index, chunk in enumerate(sqlite_chunks):
        postgresql_chunk = postgresql_repository.insert_chunk(
            document_id=postgresql_document["id"],
            text=chunk["text"],
            chunk_index=index,
        )

        embedding = embedder(chunk["text"], model=embedding_model)

        postgresql_repository.upsert_embedding(
            chunk_id=postgresql_chunk["id"],
            embedding=embedding,
            model=embedding_model,
        )

        embedding_count = embedding_count + 1

    return {
        "created": True,
        "skipped": False,
        "reason": "",
        "title": title,
        "chunk_count": len(sqlite_chunks),
        "embedding_count": embedding_count,
        "source": source,
    }


def main():
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

            result = migrate_one_sqlite_document_to_postgresql(
                sqlite_repository=sqlite_repository,
                postgresql_repository=postgresql_repository,
                title=SQLITE_MIGRATION_SAMPLE_TITLE,
                embedder=embed_with_ollama,
                embedding_model=EMBEDDING_MODEL,
            )

        print_migration_result(result)
    finally:
        sqlite_connection.close()


if __name__ == "__main__":
    main()