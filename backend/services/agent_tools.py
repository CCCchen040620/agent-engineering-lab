"""Agent tools for the knowledge base."""

from backend.services.sqlite_document_repository import (
    create_connection,
    create_documents_table,
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