from fastapi import APIRouter

#from week02.document_dict import document
#from week02.document_list import documents
from week02.load_documents import load_documents
from week04.settings import DOCUMENTS_JSON_PATH
from week05.models import Document
from backend.services.document_service import filter_documents


router = APIRouter(prefix="/api/v1")


@router.get("/documents", response_model=list[Document])
def list_documents(indexed_only: bool = False, file_type: str | None = None):
    documents = load_documents(DOCUMENTS_JSON_PATH)

    return filter_documents(
        documents,
        indexed_only=indexed_only,
        file_type=file_type,
    )