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

    missing_document_titles = []

    for document in sqlite_documents:
        if document["title"] not in postgresql_titles:
            missing_document_titles.append(document["title"])

    return {
        "sqlite_document_count": len(sqlite_documents),
        "sqlite_chunk_count": len(sqlite_chunks),
        "postgresql_document_count": len(postgresql_documents),
        "postgresql_chunk_count": len(postgresql_chunks),
        "missing_document_titles": missing_document_titles,
    }


def print_migration_preview(preview: dict):
    print("SQLite -> PostgreSQL 迁移预览")
    print("SQLite 文档数量：", preview["sqlite_document_count"])
    print("SQLite chunks 数量：", preview["sqlite_chunk_count"])
    print("PostgreSQL 文档数量：", preview["postgresql_document_count"])
    print("PostgreSQL chunks 数量：", preview["postgresql_chunk_count"])
    print("-" * 50)

    if len(preview["missing_document_titles"]) == 0:
        print("SQLite 中没有发现尚未出现在 PostgreSQL 的文档。")
        return

    print("SQLite 中尚未出现在 PostgreSQL 的文档：")

    for title in preview["missing_document_titles"]:
        print("-", title)