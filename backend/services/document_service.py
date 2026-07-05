import json


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