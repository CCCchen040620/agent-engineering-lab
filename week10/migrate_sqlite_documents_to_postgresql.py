from week10.migrate_one_sqlite_document_to_postgresql import (
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