from fastapi import APIRouter

from backend.services.rag_backend_capability_service import (
    list_rag_backend_capabilities,
)


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
            "sqlite_upload_txt_document",
            "sqlite_get_document_by_id",
            "sqlite_delete_document_by_id",
            "sqlite_chat_with_citations",
            "sqlite_vector_retrieval",
            "sqlite_llm_chat_with_local_qwen",
            "similarity_min_score_filter",
            "local_llm_failure_fallback",
            "sqlite_feedback_storage",
            "sqlite_feedback_list",
            "sqlite_feedback_summary",
            "sqlite_list_document_chunks",
            "embedding_retrieval",
            "precomputed_embedding_retrieval",
            "chunk_embedding_backfill",
            "document_embedding_status",
            "simple_agent_chat",
            "agent_tool_workflow",
            "system_status_diagnostics",
            "postgresql_status_diagnostics",
            "basic_in_memory_rate_limiting",
            "rag_backend_capability_matrix",
        ],
        "rag_backends": list_rag_backend_capabilities(),
    }
