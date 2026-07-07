from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_info_endpoint():
    response = client.get("/api/v1/info")

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Enterprise Knowledge Base Agent"
    assert data["version"] == "0.1.0"
    assert "legacy_file_chat_with_citations" in data["features"]
    assert "legacy_file_refusal_for_unknown_questions" in data["features"]
    assert "legacy_json_list_documents" in data["features"]
    assert "legacy_json_create_document" in data["features"]
    assert "legacy_json_delete_document_by_id" in data["features"]
    assert "sqlite_chat_with_citations" in data["features"]
    assert "sqlite_list_documents" in data["features"]
    assert "sqlite_create_document" in data["features"]
    assert "sqlite_upload_txt_document" in data["features"]
    assert "sqlite_delete_document_by_id" in data["features"]
    assert "sqlite_chat_with_citations" in data["features"]
    assert "sqlite_vector_retrieval" in data["features"]
    assert "sqlite_llm_chat_with_local_qwen" in data["features"]
    assert "similarity_min_score_filter" in data["features"]
    assert "local_llm_failure_fallback" in data["features"]
    assert "sqlite_feedback_storage" in data["features"]
    assert "sqlite_feedback_list" in data["features"]
    assert "sqlite_feedback_summary" in data["features"]
    assert "sqlite_list_document_chunks" in data["features"]
    assert "embedding_retrieval" in data["features"]
    assert "precomputed_embedding_retrieval" in data["features"]
    assert "chunk_embedding_backfill" in data["features"]
    assert "document_embedding_status" in data["features"]
