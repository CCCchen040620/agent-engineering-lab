from fastapi import APIRouter

#from week02.document_dict import document
#from week02.document_list import documents
from week02.load_documents import load_documents
from week04.settings import DOCUMENTS_JSON_PATH
from week05.models import Document


router = APIRouter(prefix="/api/v1")


@router.get("/documents", response_model=list[Document])
def list_documents(indexed_only: bool = False):
    documents = load_documents(DOCUMENTS_JSON_PATH)

    if indexed_only:
        results = []

        for document in documents:
            if document["is_indexed"]:
                results.append(document)
        return results

    return documents