from backend.services.sqlite_document_repository import (
    create_chunks_table,
    create_documents_table,
    insert_chunk_to_db,
    try_insert_document_to_db,
)


def split_long_text(text: str, max_chunk_size: int) -> list[str]:
    chunks = []

    for start in range(0, len(text), max_chunk_size):
        chunks.append(text[start : start + max_chunk_size])

    return chunks


def split_text_into_chunks(
    content: str,
    max_chunk_size: int = 120,
) -> list[str]:
    normalized_content = content.replace("\n", "。")

    for separator in ["！", "？", "!", "?"]:
        normalized_content = normalized_content.replace(separator, "。")

    raw_chunks = normalized_content.split("。")

    chunks = []

    for raw_chunk in raw_chunks:
        chunk = raw_chunk.strip()

        if chunk == "":
            continue

        chunk = chunk + "。"

        if len(chunk) <= max_chunk_size:
            chunks.append(chunk)
        else:
            chunks.extend(split_long_text(chunk, max_chunk_size))

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