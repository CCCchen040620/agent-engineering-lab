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
        "missing_document_titles": ["请假制度"],
    }