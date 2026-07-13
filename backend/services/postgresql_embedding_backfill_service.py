from backend.config import EMBEDDING_MODEL
from backend.services.ollama_embedding_service import embed_with_ollama
from backend.services.postgresql_document_repository import (
    list_all_chunks_from_postgresql,
)
from backend.services.postgresql_embedding_repository import (
    find_chunk_embedding_by_chunk_id_from_postgresql,
    upsert_chunk_embedding_to_postgresql,
)


def backfill_missing_postgresql_chunk_embeddings(
    connection,
    model: str = EMBEDDING_MODEL,
) -> dict:
    """Generate embeddings only for PostgreSQL chunks that do not have one."""
    chunks = list_all_chunks_from_postgresql(connection)

    updated = 0
    skipped = 0

    for chunk in chunks:
        existing_embedding = find_chunk_embedding_by_chunk_id_from_postgresql(
            connection,
            chunk_id=chunk["id"],
        )

        if existing_embedding is not None:
            skipped = skipped + 1
            continue

        embedding = embed_with_ollama(chunk["text"], model=model)

        upsert_chunk_embedding_to_postgresql(
            connection,
            chunk_id=chunk["id"],
            embedding=embedding,
            model=model,
        )

        updated = updated + 1

    return {
        "total_chunks": len(chunks),
        "updated": updated,
        "skipped": skipped,
        "model": model,
    }
