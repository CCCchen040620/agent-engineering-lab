import json

from week05.models import Document, DocumentCreateRequest


def save_documents(file_path: str, documents: list[dict]) -> None:
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(documents, file, ensure_ascii=False, indent=2)


def filter_documents(
    documents: list[dict],
    indexed_only: bool = False,
    file_type: str | None = None,
) -> list[dict]:
    results = []

    for document in documents:
        if indexed_only and not document["is_indexed"]:
            continue

        if file_type is not None and document["file_type"] != file_type:
            continue

        results.append(document)

    return results


def find_document_by_title(documents: list[dict], title: str) -> dict | None:
    for document in documents:
        if document["title"] == title:
            return document

    return None


def delete_document_by_title(documents: list[dict], title: str) -> tuple[list[dict], bool]:
    results = []
    deleted = False

    for document in documents:
        if document["title"] == title:
            deleted = True
            continue

        results.append(document)

    return results, deleted


def add_document(
    documents: list[dict],
    request: DocumentCreateRequest,
) -> tuple[list[dict], Document | None]:
    existing_document = find_document_by_title(documents, request.title)

    if existing_document is not None:
        return documents, None

    document = Document(
        title=request.title,
        file_type=request.file_type,
        chunk_count=request.chunk_count,
        is_indexed=request.is_indexed,
    )

    results = documents + [document.model_dump()]

    return results, document