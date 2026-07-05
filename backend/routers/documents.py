from fastapi import APIRouter

#from week02.document_dict import document
#from week02.document_list import documents
from week02.load_documents import load_documents
from week04.settings import DOCUMENTS_JSON_PATH
from week05.models import Document


router = APIRouter(prefix="/api/v1")


@router.get("/documents", response_model=list[Document])
def list_documents(indexed_only: bool = False, file_type: str | None = None):
    documents = load_documents(DOCUMENTS_JSON_PATH)
    results = []

    for document in documents:
        if indexed_only and not document["is_indexed"]:
            continue

        if file_type is not None and document["file_type"] != file_type:
            continue

        results.append(document)

    return results