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