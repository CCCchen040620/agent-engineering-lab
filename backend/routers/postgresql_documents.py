import psycopg
from fastapi import APIRouter, Depends, HTTPException

from backend.config import DATABASE_URL
from backend.services.database_url_service import is_postgresql_database
from backend.services.postgresql_document_repository import (
    list_documents_from_postgresql,
)
from backend.services.postgresql_schema_service import (
    initialize_postgresql_knowledge_schema,
)
from week05.models import Document


router = APIRouter(prefix="/api/v1/postgresql")


def get_postgresql_database_url() -> str:
    return DATABASE_URL


@router.get("/documents", response_model=list[Document])
def list_postgresql_documents(
    database_url: str = Depends(get_postgresql_database_url),
):
    if not is_postgresql_database(database_url):
        raise HTTPException(
            status_code=400,
            detail="DATABASE_URL must be a PostgreSQL URL.",
        )

    with psycopg.connect(database_url) as connection:
        initialize_postgresql_knowledge_schema(connection)
        documents = list_documents_from_postgresql(connection)

    return documents