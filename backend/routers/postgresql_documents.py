import psycopg
from fastapi import APIRouter, Depends, HTTPException, Query
from backend.services.postgresql_vector_search_repository import (
    search_chunks_by_vector_from_postgresql,
)
from backend.services.postgresql_natural_language_search_service import (
    search_postgresql_chunks_by_question,
)
from backend.config import DATABASE_URL
from backend.services.database_url_service import is_postgresql_database
from backend.services.postgresql_document_repository import (
    summarize_document_sources_from_postgresql,
    summarize_documents_by_source_from_postgresql,
    delete_documents_by_source_from_postgresql,
    list_chunks_by_document_from_postgresql,
    list_documents_from_postgresql,
)
from backend.services.postgresql_embedding_repository import (
    summarize_document_embedding_status_from_postgresql,
)
from backend.services.postgresql_embedding_backfill_service import (
    backfill_missing_postgresql_chunk_embeddings,
)
from backend.services.postgresql_schema_service import (
    initialize_postgresql_knowledge_schema,
)
from backend.services.postgresql_document_indexing_service import (
    PostgreSQLDocumentIndexingError,
    create_postgresql_document_with_chunks_and_embeddings,
)
from week05.models import (
    Chunk,
    Document,
    DocumentCreateWithContentRequest,
    PostgreSQLDocument,
    QuestionSearchRequest,
    QuestionSearchResponse,
    VectorSearchRequest,
    VectorSearchResult,
)


router = APIRouter(prefix="/api/v1/postgresql")


def get_postgresql_database_url() -> str:
    return DATABASE_URL


@router.get("/documents", response_model=list[PostgreSQLDocument])
def list_postgresql_documents(
    source: str | None = Query(default=None),
    database_url: str = Depends(get_postgresql_database_url),
):
    if not is_postgresql_database(database_url):
        raise HTTPException(
            status_code=400,
            detail="DATABASE_URL must be a PostgreSQL URL.",
        )

    with psycopg.connect(database_url) as connection:
        initialize_postgresql_knowledge_schema(connection)
        documents = list_documents_from_postgresql(connection, source=source)

    return documents


@router.get("/documents/source-summary")
def summarize_postgresql_document_sources(
    database_url: str = Depends(get_postgresql_database_url),
):
    if not is_postgresql_database(database_url):
        raise HTTPException(
            status_code=400,
            detail="DATABASE_URL must be a PostgreSQL URL.",
        )

    with psycopg.connect(database_url) as connection:
        initialize_postgresql_knowledge_schema(connection)
        summaries = summarize_document_sources_from_postgresql(connection)

    return summaries


@router.get("/documents/evaluation/cleanup-preview")
def preview_postgresql_evaluation_documents_cleanup(
    database_url: str = Depends(get_postgresql_database_url),
):
    if not is_postgresql_database(database_url):
        raise HTTPException(
            status_code=400,
            detail="DATABASE_URL must be a PostgreSQL URL.",
        )

    with psycopg.connect(database_url) as connection:
        initialize_postgresql_knowledge_schema(connection)
        summary = summarize_documents_by_source_from_postgresql(
            connection,
            source="evaluation",
        )

    return summary

    
@router.delete("/documents/evaluation")
def delete_postgresql_evaluation_documents(
    confirm: bool = Query(default=False),
    database_url: str = Depends(get_postgresql_database_url),
):
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Deleting evaluation documents requires confirm=true.",
        )

    if not is_postgresql_database(database_url):
        raise HTTPException(
            status_code=400,
            detail="DATABASE_URL must be a PostgreSQL URL.",
        )

    with psycopg.connect(database_url) as connection:
        initialize_postgresql_knowledge_schema(connection)
        deleted_count = delete_documents_by_source_from_postgresql(
            connection,
            source="evaluation",
        )

    return {
        "message": "评测文档已清理。",
        "deleted_count": deleted_count,
    }


@router.get("/documents/{document_id}/chunks", response_model=list[Chunk])
def list_postgresql_document_chunks(
    document_id: int,
    database_url: str = Depends(get_postgresql_database_url),
):
    if not is_postgresql_database(database_url):
        raise HTTPException(
            status_code=400,
            detail="DATABASE_URL must be a PostgreSQL URL.",
        )

    with psycopg.connect(database_url) as connection:
        initialize_postgresql_knowledge_schema(connection)
        chunks = list_chunks_by_document_from_postgresql(
            connection,
            document_id=document_id,
        )

    return chunks


@router.get("/documents/embedding-status")
def list_postgresql_embedding_status(
    database_url: str = Depends(get_postgresql_database_url),
):
    if not is_postgresql_database(database_url):
        raise HTTPException(
            status_code=400,
            detail="DATABASE_URL must be a PostgreSQL URL.",
        )

    with psycopg.connect(database_url) as connection:
        initialize_postgresql_knowledge_schema(connection)
        statuses = summarize_document_embedding_status_from_postgresql(
            connection,
        )

    return statuses


@router.post("/embeddings/backfill")
def backfill_postgresql_embeddings(
    database_url: str = Depends(get_postgresql_database_url),
):
    if not is_postgresql_database(database_url):
        raise HTTPException(
            status_code=400,
            detail="DATABASE_URL must be a PostgreSQL URL.",
        )

    with psycopg.connect(database_url) as connection:
        initialize_postgresql_knowledge_schema(connection)
        try:
            result = backfill_missing_postgresql_chunk_embeddings(connection)
        except Exception as error:
            raise HTTPException(
                status_code=503,
                detail=f"PostgreSQL embedding 回填失败：{error}",
            ) from error

    return result


@router.post(
    "/documents/with-content",
    response_model=PostgreSQLDocument,
    status_code=201,
)
def create_postgresql_document_with_content(
    request: DocumentCreateWithContentRequest,
    database_url: str = Depends(get_postgresql_database_url),
):
    if not is_postgresql_database(database_url):
        raise HTTPException(
            status_code=400,
            detail="DATABASE_URL must be a PostgreSQL URL.",
        )

    with psycopg.connect(database_url) as connection:
        initialize_postgresql_knowledge_schema(connection)
        try:
            result = create_postgresql_document_with_chunks_and_embeddings(
                connection,
                title=request.title,
                file_type=request.file_type,
                content=request.content,
            )
        except PostgreSQLDocumentIndexingError as error:
            raise HTTPException(
                status_code=503,
                detail=str(error),
            ) from error

    if result is None:
        raise HTTPException(
            status_code=409,
            detail="文档创建失败，可能是标题重复或内容为空。",
        )

    return result["document"]


@router.post("/search/vector", response_model=list[VectorSearchResult])
def search_postgresql_chunks_by_vector(
    request: VectorSearchRequest,
    database_url: str = Depends(get_postgresql_database_url),
):
    if not is_postgresql_database(database_url):
        raise HTTPException(
            status_code=400,
            detail="DATABASE_URL must be a PostgreSQL URL.",
        )

    with psycopg.connect(database_url) as connection:
        initialize_postgresql_knowledge_schema(connection)
        results = search_chunks_by_vector_from_postgresql(
            connection,
            query_embedding=request.embedding,
            top_k=request.top_k,
        )

    return results


@router.post("/search/question", response_model=QuestionSearchResponse)
def search_postgresql_chunks_by_natural_language_question(
    request: QuestionSearchRequest,
    database_url: str = Depends(get_postgresql_database_url),
):
    if not is_postgresql_database(database_url):
        raise HTTPException(
            status_code=400,
            detail="DATABASE_URL must be a PostgreSQL URL.",
        )

    with psycopg.connect(database_url) as connection:
        initialize_postgresql_knowledge_schema(connection)
        result = search_postgresql_chunks_by_question(
            connection,
            question=request.question,
            top_k=request.top_k,
            min_score=request.min_score,
        )

    return result
