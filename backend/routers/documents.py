from fastapi import APIRouter, Depends, HTTPException

#from week02.document_dict import document
#from week02.document_list import documents
from week02.load_documents import load_documents
from week04.settings import DOCUMENTS_JSON_PATH
from week05.models import Document, DocumentCreateRequest
from backend.services.document_service import (
    add_document,
    delete_document_by_title,
    filter_documents,
    find_document_by_title,
    save_documents,
    find_document_by_id,
)


router = APIRouter(prefix="/api/v1")

def get_documents_file_path() -> str:
    return DOCUMENTS_JSON_PATH


@router.get("/documents", response_model=list[Document])
def list_documents(
    indexed_only: bool = False, 
    file_type: str | None = None, 
    file_path: str = Depends(get_documents_file_path),
):
    documents = load_documents(file_path)

    return filter_documents(
        documents,
        indexed_only=indexed_only,
        file_type=file_type,
    )


@router.get("/documents/by-id/{document_id}", response_model=Document)
def get_document_by_id(
    document_id: int,
    file_path: str = Depends(get_documents_file_path),
):
    documents = load_documents(file_path)
    document = find_document_by_id(documents, document_id)

    if document is None:
        raise HTTPException(status_code=404, detail="文档不存在。")

    return document


@router.get("/documents/{title}", response_model=Document)
def get_document(
    title: str,
    file_path: str = Depends(get_documents_file_path),
):
    documents = load_documents(file_path)
    document = find_document_by_title(documents, title)

    if document is None:
        raise HTTPException(status_code=404, detail="文档不存在。")

    return document


@router.post("/documents", response_model=Document, status_code=201)
def create_document(
    request: DocumentCreateRequest,
    file_path: str = Depends(get_documents_file_path),
):
    documents = load_documents(file_path)

    results, document = add_document(documents, request)

    if document is None:
        raise HTTPException(status_code=409, detail="文档已存在。")

    save_documents(file_path, results)

    return document


@router.delete("/documents/{title}")
def delete_document(
    title: str,
    file_path: str = Depends(get_documents_file_path),
):
    documents = load_documents(file_path)

    results, deleted = delete_document_by_title(documents, title)

    if not deleted:
        raise HTTPException(status_code=404, detail="文档不存在。")

    save_documents(file_path, results)

    return {"message": "文档已删除。", "title": title} 