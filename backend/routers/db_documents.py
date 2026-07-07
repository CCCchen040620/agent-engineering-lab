"""SQLite-backed API routes for document management and RAG chat."""
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from backend.config import DEFAULT_MIN_SCORE, DEFAULT_TOP_K
from backend.services.document_indexing_service import (
    create_document_with_chunks_and_embeddings,
    split_text_into_chunks,
)
from backend.services.sqlite_qa_service import build_sqlite_chat_response
from backend.services.sqlite_llm_qa_service import build_sqlite_llm_chat_response
from backend.services.sqlite_document_repository import (
    create_connection,
    create_documents_table,
    create_chunks_table,
    list_documents_from_db_filtered,
    try_insert_document_to_db,
    find_document_from_db_by_id,
    delete_document_from_db_by_id,
    list_chunks_by_document_id,
)
from week04.settings import SQLITE_DATABASE_PATH
from week05.models import (
    ChatRequest,
    ChatResponse,
    Document,
    DocumentCreateRequest,
    DocumentCreateWithContentRequest,
    Chunk,
)


router = APIRouter(prefix="/api/v1/db")


def get_database_path() -> str:
    return SQLITE_DATABASE_PATH


@router.get("/documents", response_model=list[Document])
def list_db_documents(
    indexed_only: bool = False,
    file_type: str | None = None,
    database_path: str = Depends(get_database_path),
):
    connection = create_connection(database_path)

    create_documents_table(connection)
    documents = list_documents_from_db_filtered(
        connection,
        indexed_only=indexed_only,
        file_type=file_type,
    )

    connection.close()

    return documents


@router.post("/documents", response_model=Document, status_code=201)
def create_db_document(
    request: DocumentCreateRequest,
    database_path: str = Depends(get_database_path),
):
    connection = create_connection(database_path)

    create_documents_table(connection)

    document = try_insert_document_to_db(
        connection,
        title=request.title,
        file_type=request.file_type,
        chunk_count=request.chunk_count,
        is_indexed=request.is_indexed,
    )

    connection.close()

    if document is None:
        raise HTTPException(status_code=409, detail="文档已存在。")

    return document


@router.post("/documents/with-content", response_model=Document, status_code=201)
def create_db_document_with_content(
    request: DocumentCreateWithContentRequest,
    database_path: str = Depends(get_database_path),
):
    chunks = split_text_into_chunks(request.content)

    if chunks == []:
        raise HTTPException(status_code=422, detail="文档正文没有有效内容。")

    connection = create_connection(database_path)

    document = create_document_with_chunks_and_embeddings(
        connection,
        title=request.title,
        file_type=request.file_type,
        content=request.content,
    )

    connection.close()

    if document is None:
        raise HTTPException(status_code=409, detail="文档已存在。")

    return document


@router.post("/documents/upload-text", response_model=Document, status_code=201)
async def upload_text_document(
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    database_path: str = Depends(get_database_path),
):
    filename = file.filename or "uploaded.txt"

    if not filename.lower().endswith(".txt"):
        raise HTTPException(status_code=422, detail="仅支持 txt 文件。")

    content_bytes = await file.read()

    try:
        content = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=422,
            detail="文件读取失败，请上传 UTF-8 编码的 txt 文件。",
        )

    chunks = split_text_into_chunks(content)

    if chunks == []:
        raise HTTPException(status_code=422, detail="文档正文没有有效内容。")

    if title is None or title.strip() == "":
        document_title = filename.rsplit(".", 1)[0]
    else:
        document_title = title.strip()

    connection = create_connection(database_path)

    document = create_document_with_chunks_and_embeddings(
        connection,
        title=document_title,
        file_type="txt",
        content=content,
    )

    connection.close()

    if document is None:
        raise HTTPException(status_code=409, detail="文档已存在。")

    return document


@router.get("/documents/{document_id}", response_model=Document)
def get_db_document_by_id(
    document_id: int,
    database_path: str = Depends(get_database_path),
):
    connection = create_connection(database_path)

    create_documents_table(connection)
    document = find_document_from_db_by_id(connection, document_id)

    connection.close()

    if document is None:
        raise HTTPException(status_code=404, detail="文档不存在。")

    return document


@router.get("/documents/{document_id}/chunks", response_model=list[Chunk])
def list_db_document_chunks(
    document_id: int,
    database_path: str = Depends(get_database_path),
):
    connection = create_connection(database_path)

    create_documents_table(connection)
    create_chunks_table(connection)

    document = find_document_from_db_by_id(connection, document_id)

    if document is None:
        connection.close()
        raise HTTPException(status_code=404, detail="文档不存在。")

    chunks = list_chunks_by_document_id(connection, document_id)

    connection.close()

    return chunks


@router.delete("/documents/{document_id}")
def delete_db_document_by_id(
    document_id: int,
    database_path: str = Depends(get_database_path),
):
    connection = create_connection(database_path)

    create_documents_table(connection)
    deleted = delete_document_from_db_by_id(connection, document_id)

    connection.close()

    if not deleted:
        raise HTTPException(status_code=404, detail="文档不存在。")

    return {"message": "文档已删除。", "id": document_id}


@router.post("/chat", response_model=ChatResponse)
def sqlite_chat(
    request: ChatRequest,
    top_k: int = Query(default=DEFAULT_TOP_K, ge=1, le=5),
    mode: str = "keyword",
    database_path: str = Depends(get_database_path),
):
    return build_sqlite_chat_response(
        request.question,
        database_path=database_path,
        top_k=top_k,
        mode=mode,
    )


@router.post("/chat/llm", response_model=ChatResponse)
def sqlite_llm_chat(
    request: ChatRequest,
    top_k: int = Query(default=DEFAULT_TOP_K, ge=1, le=5),
    mode: str = "vector",
    min_score: float = Query(default=DEFAULT_MIN_SCORE, ge=0, le=1),
    database_path: str = Depends(get_database_path),
):
    return build_sqlite_llm_chat_response(
        request.question,
        database_path=database_path,
        top_k=top_k,
        mode=mode,
        min_score=min_score,
    )
