from week11.validate_postgresql_document_ingestion import (
    search_results_include_document,
    top_result_matches_document,
    validate_postgresql_document_ingestion,
)


class FakeConnection:
    pass


def test_top_result_matches_document():
    results = [
        {
            "document_title": "员工手册",
            "text": "新员工入职后需要在 30 天内完成安全培训。",
        }
    ]

    assert top_result_matches_document(results, "员工手册") is True
    assert top_result_matches_document(results, "请假制度") is False
    assert top_result_matches_document([], "员工手册") is False


def test_search_results_include_document():
    results = [
        {
            "document_title": "请假制度",
            "text": "员工请假需要提前在系统中提交申请。",
        },
        {
            "document_title": "员工手册",
            "text": "新员工入职后需要在 30 天内完成安全培训。",
        },
    ]

    assert search_results_include_document(results, "员工手册") is True
    assert search_results_include_document(results, "设备借用制度") is False


def test_validate_postgresql_document_ingestion_passes(monkeypatch):
    connection = FakeConnection()

    monkeypatch.setattr(
        "week11.validate_postgresql_document_ingestion."
        "find_document_by_title_from_postgresql",
        lambda connection, title: {
            "id": 1,
            "title": title,
            "file_type": "md",
            "chunk_count": 2,
            "is_indexed": True,
            "source": "production",
        },
    )
    monkeypatch.setattr(
        "week11.validate_postgresql_document_ingestion."
        "list_chunks_by_document_from_postgresql",
        lambda connection, document_id: [
            {
                "id": 10,
                "document_id": document_id,
                "text": "新员工入职后需要在 30 天内完成安全培训。",
                "chunk_index": 0,
            },
            {
                "id": 11,
                "document_id": document_id,
                "text": "员工每天需要完成 8 小时工作。",
                "chunk_index": 1,
            },
        ],
    )
    monkeypatch.setattr(
        "week11.validate_postgresql_document_ingestion."
        "find_embedding_status_by_document_title",
        lambda connection, title: {
            "document_id": 1,
            "title": title,
            "chunk_count": 2,
            "embedding_count": 2,
            "is_embedding_complete": True,
        },
    )

    def fake_searcher(connection, question, top_k, min_score):
        return {
            "question": question,
            "embedding_size": 1024,
            "results": [
                {
                    "chunk_id": 10,
                    "document_id": 1,
                    "document_title": "员工手册",
                    "text": "新员工入职后需要在 30 天内完成安全培训。",
                    "score": 0.91,
                }
            ],
        }

    result = validate_postgresql_document_ingestion(
        connection,
        title="员工手册",
        question="新员工什么时候完成安全培训？",
        top_k=3,
        min_score=0.6,
        searcher=fake_searcher,
    )

    assert result["passed"] is True
    assert result["failure_reason"] == ""
    assert result["document_found"] is True
    assert result["chunk_count"] == 2
    assert result["embedding_count"] == 2
    assert result["is_embedding_complete"] is True
    assert result["retrieved_expected_document"] is True
    assert result["top1_matches_document"] is True


def test_validate_postgresql_document_ingestion_fails_when_document_missing(
    monkeypatch,
):
    connection = FakeConnection()

    monkeypatch.setattr(
        "week11.validate_postgresql_document_ingestion."
        "find_document_by_title_from_postgresql",
        lambda connection, title: None,
    )

    result = validate_postgresql_document_ingestion(
        connection,
        title="不存在的文档",
        question="测试问题",
    )

    assert result["passed"] is False
    assert result["failure_reason"] == "document_not_found"
    assert result["document_found"] is False
    assert result["retrieval_count"] == 0


def test_validate_postgresql_document_ingestion_fails_when_embedding_incomplete(
    monkeypatch,
):
    connection = FakeConnection()

    monkeypatch.setattr(
        "week11.validate_postgresql_document_ingestion."
        "find_document_by_title_from_postgresql",
        lambda connection, title: {
            "id": 1,
            "title": title,
            "file_type": "md",
            "chunk_count": 2,
            "is_indexed": True,
            "source": "production",
        },
    )
    monkeypatch.setattr(
        "week11.validate_postgresql_document_ingestion."
        "list_chunks_by_document_from_postgresql",
        lambda connection, document_id: [
            {"id": 10, "document_id": document_id, "text": "片段1", "chunk_index": 0},
            {"id": 11, "document_id": document_id, "text": "片段2", "chunk_index": 1},
        ],
    )
    monkeypatch.setattr(
        "week11.validate_postgresql_document_ingestion."
        "find_embedding_status_by_document_title",
        lambda connection, title: {
            "document_id": 1,
            "title": title,
            "chunk_count": 2,
            "embedding_count": 1,
            "is_embedding_complete": False,
        },
    )

    def fake_searcher(connection, question, top_k, min_score):
        return {
            "results": [
                {
                    "document_title": "员工手册",
                    "text": "片段1",
                    "score": 0.8,
                }
            ]
        }

    result = validate_postgresql_document_ingestion(
        connection,
        title="员工手册",
        question="测试问题",
        searcher=fake_searcher,
    )

    assert result["passed"] is False
    assert result["failure_reason"] == "embedding_incomplete"
    assert result["embedding_count"] == 1
    assert result["is_embedding_complete"] is False


def test_validate_postgresql_document_ingestion_fails_when_top1_is_wrong_document(
    monkeypatch,
):
    connection = FakeConnection()

    monkeypatch.setattr(
        "week11.validate_postgresql_document_ingestion."
        "find_document_by_title_from_postgresql",
        lambda connection, title: {
            "id": 1,
            "title": title,
            "file_type": "md",
            "chunk_count": 1,
            "is_indexed": True,
            "source": "production",
        },
    )
    monkeypatch.setattr(
        "week11.validate_postgresql_document_ingestion."
        "list_chunks_by_document_from_postgresql",
        lambda connection, document_id: [
            {"id": 10, "document_id": document_id, "text": "片段1", "chunk_index": 0},
        ],
    )
    monkeypatch.setattr(
        "week11.validate_postgresql_document_ingestion."
        "find_embedding_status_by_document_title",
        lambda connection, title: {
            "document_id": 1,
            "title": title,
            "chunk_count": 1,
            "embedding_count": 1,
            "is_embedding_complete": True,
        },
    )

    def fake_searcher(connection, question, top_k, min_score):
        return {
            "results": [
                {
                    "document_title": "其他文档",
                    "text": "其他片段",
                    "score": 0.9,
                },
                {
                    "document_title": "员工手册",
                    "text": "片段1",
                    "score": 0.8,
                },
            ]
        }

    result = validate_postgresql_document_ingestion(
        connection,
        title="员工手册",
        question="测试问题",
        searcher=fake_searcher,
    )

    assert result["passed"] is False
    assert result["failure_reason"] == "top1_document_mismatch"
    assert result["retrieved_expected_document"] is True
    assert result["top1_matches_document"] is False
