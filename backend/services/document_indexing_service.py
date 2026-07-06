from backend.services.sqlite_document_repository import (
    create_chunks_table,
    create_documents_table,
    insert_chunk_to_db,
    try_insert_document_to_db,
)


def split_text_into_chunks(content: str) -> list[str]:
    raw_chunks = content.replace("\n", "。").split("。")

    chunks = []

    for raw_chunk in raw_chunks:
        chunk = raw_chunk.strip()

        if chunk != "":
            chunks.append(chunk + "。")

    return chunks


def create_document_with_chunks(
    connection,
    title: str,
    file_type: str,
    content: str,
) -> dict | None:
    create_documents_table(connection)
    create_chunks_table(connection)

    chunks = split_text_into_chunks(content)

    document = try_insert_document_to_db(
        connection,
        title=title,
        file_type=file_type,
        chunk_count=len(chunks),
        is_indexed=len(chunks) > 0,
    )

    if document is None:
        return None

    for chunk in chunks:
        insert_chunk_to_db(
            connection,
            document_id=document["id"],
            text=chunk,
        )

    return document