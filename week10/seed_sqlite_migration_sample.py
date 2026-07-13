from backend.config import SQLITE_ADMIN_DATABASE_PATH
from backend.services.sqlite_document_repository import (
    create_chunks_table,
    create_connection,
    create_documents_table,
    find_document_from_db_by_title,
    insert_chunk_to_db,
    insert_document_to_db,
    list_chunks_by_document_id,
)


SQLITE_MIGRATION_SAMPLE_TITLE = "SQLite 迁移验收文档"
SQLITE_MIGRATION_SAMPLE_CHUNKS = [
    "SQLite 迁移测试片段一。",
    "SQLite 迁移测试片段二。",
]


def seed_sqlite_migration_sample(
    connection,
    title: str = SQLITE_MIGRATION_SAMPLE_TITLE,
    chunks: list[str] | None = None,
) -> dict:
    if chunks is None:
        chunks = SQLITE_MIGRATION_SAMPLE_CHUNKS

    create_documents_table(connection)
    create_chunks_table(connection)

    existing_document = find_document_from_db_by_title(connection, title)

    if existing_document is not None:
        existing_chunks = list_chunks_by_document_id(
            connection,
            document_id=existing_document["id"],
        )

        return {
            "created": False,
            "document": existing_document,
            "inserted_chunks": 0,
            "chunk_count": len(existing_chunks),
        }

    document = insert_document_to_db(
        connection,
        title=title,
        file_type="md",
        chunk_count=len(chunks),
        is_indexed=True,
    )

    inserted_chunks = []

    for text in chunks:
        inserted_chunks.append(
            insert_chunk_to_db(
                connection,
                document_id=document["id"],
                text=text,
            )
        )

    return {
        "created": True,
        "document": document,
        "inserted_chunks": len(inserted_chunks),
        "chunk_count": len(inserted_chunks),
    }


def print_seed_result(result: dict):
    print("SQLite 迁移样本准备完成。")
    print("是否新建文档：", result["created"])
    print("文档标题：", result["document"]["title"])
    print("文档 ID：", result["document"]["id"])
    print("新增 chunks 数量：", result["inserted_chunks"])
    print("当前 chunks 数量：", result["chunk_count"])


def main():
    connection = create_connection(SQLITE_ADMIN_DATABASE_PATH)

    try:
        result = seed_sqlite_migration_sample(connection)
    finally:
        connection.close()

    print_seed_result(result)


if __name__ == "__main__":
    main()
