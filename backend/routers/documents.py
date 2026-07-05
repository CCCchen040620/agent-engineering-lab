from fastapi import APIRouter

from week02.load_documents import load_documents
from week04.settings import DOCUMENTS_JSON_PATH


router = APIRouter(prefix="/api/v1")


@router.get("/documents")
def list_documents():
    return load_documents(DOCUMENTS_JSON_PATH)