"""Agent tools for the knowledge base."""

from backend.services.sqlite_document_repository import (
    create_chunks_table,
    create_connection,
    create_documents_table,
    find_document_from_db_by_id,
    list_chunks_by_document_id,
    list_documents_from_db_filtered,
)
from week04.settings import SQLITE_DATABASE_PATH


def list_documents_tool(database_path: str = SQLITE_DATABASE_PATH) -> dict:
    """列出知识库中的文档。"""
    connection = create_connection(database_path)

    create_documents_table(connection)

    documents = list_documents_from_db_filtered(connection)

    connection.close()

    return {
        "documents": documents,
        "count": len(documents),
    }


def read_document_chunks_tool(
    document_id: int,
    database_path: str = SQLITE_DATABASE_PATH,
) -> dict:
    """读取某一份文档的 chunks。"""
    connection = create_connection(database_path)

    create_documents_table(connection)
    create_chunks_table(connection)

    document = find_document_from_db_by_id(connection, document_id)

    if document is None:
        connection.close()

        return {
            "found": False,
            "document": None,
            "chunks": [],
        }

    chunks = list_chunks_by_document_id(connection, document_id)

    connection.close()

    return {
        "found": True,
        "document": document,
        "chunks": chunks,
    }