from week10.preview_sqlite_to_postgresql_migration import (
    preview_sqlite_to_postgresql_migration,
)


class FakeSqliteRepository:
    def list_documents(self):
        return [
            {
                "id": 1,
                "title": "员工手册",
                "file_type": "md",
                "chunk_count": 2,
                "is_indexed": True,
            },
            {
                "id": 2,
                "title": "请假制度",
                "file_type": "md",
                "chunk_count": 1,
                "is_indexed": True,
            },
        ]

    def list_all_chunks(self):
        return [
            {"id": 1, "document_id": 1, "text": "片段1"},
            {"id": 2, "document_id": 1, "text": "片段2"},
            {"id": 3, "document_id": 2, "text": "片段3"},
        ]


class FakePostgresqlRepository:
    def list_documents(self):
        return [
            {
                "id": 10,
                "title": "员工手册",
                "file_type": "md",
                "chunk_count": 2,
                "is_indexed": True,
                "source": "production",
            }
        ]

    def list_all_chunks(self):
        return [
            {"id": 10, "document_id": 10, "text": "片段1"},
            {"id": 11, "document_id": 10, "text": "片段2"},
        ]


def test_preview_sqlite_to_postgresql_migration():
    preview = preview_sqlite_to_postgresql_migration(
        sqlite_repository=FakeSqliteRepository(),
        postgresql_repository=FakePostgresqlRepository(),
    )

    assert preview == {
        "sqlite_document_count": 2,
        "sqlite_chunk_count": 3,
        "postgresql_document_count": 1,
        "postgresql_chunk_count": 2,
        "sqlite_is_empty": False,
        "message": "",
        "missing_document_titles": ["请假制度"],
        "pending_document_count": 1,
        "pending_chunk_count": 1,
        "pending_embedding_count": 1,
        "document_previews": [
            {
                "title": "员工手册",
                "sqlite_chunk_count": 2,
                "exists_in_postgresql": True,
                "will_migrate": False,
            },
            {
                "title": "请假制度",
                "sqlite_chunk_count": 1,
                "exists_in_postgresql": False,
                "will_migrate": True,
            },
        ],
    }


class EmptySqliteRepository:
    def list_documents(self):
        return []

    def list_all_chunks(self):
        return []


def test_preview_sqlite_to_postgresql_migration_reports_empty_sqlite():
    preview = preview_sqlite_to_postgresql_migration(
        sqlite_repository=EmptySqliteRepository(),
        postgresql_repository=FakePostgresqlRepository(),
    )

    assert preview["sqlite_document_count"] == 0
    assert preview["sqlite_chunk_count"] == 0
    assert preview["sqlite_is_empty"] is True
    assert preview["message"] == "SQLite 中暂无可迁移文档。"
    assert preview["missing_document_titles"] == []
    assert preview["pending_document_count"] == 0
    assert preview["pending_chunk_count"] == 0
    assert preview["pending_embedding_count"] == 0
    assert preview["document_previews"] == []