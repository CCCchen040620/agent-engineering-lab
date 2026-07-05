from fastapi import APIRouter

from backend.services.sqlite_document_repository import (
    create_connection,
    create_documents_table,
    list_documents_from_db,
)
from week04.settings import SQLITE_DATABASE_PATH
from week05.models import Document
from backend.services.document_service import filter_documents


router = APIRouter(prefix="/api/v1/db")


def get_database_path() -> str:
    return SQLITE_DATABASE_PATH


@router.get("/documents", response_model=list[Document])
def list_db_documents(indexed_only: bool = False, file_type: str | None = None):
    connection = create_connection(get_database_path())

    create_documents_table(connection)
    documents = list_documents_from_db(connection)

    connection.close()

    return filter_documents(
        documents,
        indexed_only=indexed_only,
        file_type=file_type,
    )