from fastapi import APIRouter


router = APIRouter(prefix="/api/v1")


@router.get("/info")
def get_info():
    return {
        "name": "Enterprise Knowledge Base Agent",
        "version": "0.1.0",
        "features": [
            "health_check",
            "legacy_file_chat_with_citations",
            "legacy_file_refusal_for_unknown_questions",
            "legacy_json_list_documents",
            "legacy_json_filter_documents",
            "legacy_json_get_document_by_id",
            "legacy_json_create_document",
            "legacy_json_delete_document_by_id",
            "sqlite_list_documents",
            "sqlite_filter_documents",
            "sqlite_create_document",
            "sqlite_get_document_by_id",
            "sqlite_delete_document_by_id",
            "sqlite_chat_with_citations",
            "sqlite_vector_retrieval",
            "sqlite_llm_chat_with_local_qwen",
            "similarity_min_score_filter",
            "local_llm_failure_fallback",
        ],
    }