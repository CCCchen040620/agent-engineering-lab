from fastapi import APIRouter

from week02.load_documents import load_documents
from week04.settings import DOCUMENTS_JSON_PATH
from week05.models import Document


router = APIRouter(prefix="/api/v1")


@router.get("/documents", response_model=list[Document])
def list_documents():
    return load_documents(DOCUMENTS_JSON_PATH)