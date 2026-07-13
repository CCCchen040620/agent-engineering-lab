from week10.migrate_sqlite_documents_to_postgresql import (
    migrate_sqlite_documents_to_postgresql,
)


class FakeSqliteRepository:
    def __init__(self):
        self.documents = [
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

        self.chunks = {
            1: [
                {"id": 1, "document_id": 1, "text": "员工每天需要完成 8 小时工作。"},
                {"id": 2, "document_id": 1, "text": "新员工需要完成安全培训。"},
            ],
            2: [
                {"id": 3, "document_id": 2, "text": "请假需要提前提交申请。"},
            ],
        }

    def list_documents(self):
        return self.documents

    def find_document_by_title(self, title):
        for document in self.documents:
            if document["title"] == title:
                return document

        return None

    def list_chunks_by_document_id(self, document_id):
        return self.chunks.get(document_id, [])


class FakePostgresqlRepository:
    def __init__(self):
        self.existing_titles = {"员工手册"}
        self.inserted_documents = []
        self.inserted_chunks = []
        self.inserted_embeddings = []

    def find_document_by_title(self, title):
        if title in self.existing_titles:
            return {"id": 10, "title": title}

        return None

    def insert_document(self, title, file_type, chunk_count, is_indexed, source):
        document = {
            "id": 100 + len(self.inserted_documents),
            "title": title,
            "file_type": file_type,
            "chunk_count": chunk_count,
            "is_indexed": is_indexed,
            "source": source,
        }
        self.inserted_documents.append(document)
        return document

    def insert_chunk(self, document_id, text, chunk_index):
        chunk = {
            "id": 200 + len(self.inserted_chunks),
            "document_id": document_id,
            "text": text,
            "chunk_index": chunk_index,
        }
        self.inserted_chunks.append(chunk)
        return chunk

    def upsert_embedding(self, chunk_id, embedding, model):
        self.inserted_embeddings.append(
            {
                "chunk_id": chunk_id,
                "embedding": embedding,
                "model": model,
            }
        )


def test_migrate_sqlite_documents_to_postgresql_skips_existing_documents():
    sqlite_repository = FakeSqliteRepository()
    postgresql_repository = FakePostgresqlRepository()

    result = migrate_sqlite_documents_to_postgresql(
        sqlite_repository=sqlite_repository,
        postgresql_repository=postgresql_repository,
        embedder=lambda text, model: [0.1, 0.2],
        embedding_model="fake-model",
        confirm=True,
    )

    assert result["total_sqlite_documents"] == 2
    assert result["created_document_count"] == 1
    assert result["skipped_document_count"] == 1
    assert result["migrated_chunk_count"] == 1
    assert result["embedding_count"] == 1
    assert result["source"] == "migration"
    assert result["confirmed"] is True
    assert result["blocked"] is False

    assert result["items"][0]["title"] == "员工手册"
    assert result["items"][0]["skipped"] is True
    assert result["items"][0]["reason"] == "postgresql_document_already_exists"

    assert result["items"][1]["title"] == "请假制度"
    assert result["items"][1]["created"] is True
    assert result["items"][1]["chunk_count"] == 1
    assert result["items"][1]["embedding_count"] == 1


class EmptySqliteRepository:
    def list_documents(self):
        return []


def test_migrate_sqlite_documents_to_postgresql_handles_empty_sqlite():
    result = migrate_sqlite_documents_to_postgresql(
        sqlite_repository=EmptySqliteRepository(),
        postgresql_repository=FakePostgresqlRepository(),
        embedder=lambda text, model: [0.1, 0.2],
        embedding_model="fake-model",
        confirm=True,
    )

    assert result["total_sqlite_documents"] == 0
    assert result["created_document_count"] == 0
    assert result["skipped_document_count"] == 0
    assert result["migrated_chunk_count"] == 0
    assert result["embedding_count"] == 0
    assert result["items"] == []
    assert result["confirmed"] is True
    assert result["blocked"] is False


def test_migrate_sqlite_documents_to_postgresql_requires_confirm():
    sqlite_repository = FakeSqliteRepository()
    postgresql_repository = FakePostgresqlRepository()

    result = migrate_sqlite_documents_to_postgresql(
        sqlite_repository=sqlite_repository,
        postgresql_repository=postgresql_repository,
        embedder=lambda text, model: [0.1, 0.2],
        embedding_model="fake-model",
    )

    assert result == {
        "confirmed": False,
        "blocked": True,
        "reason": "confirm_required",
        "total_sqlite_documents": 0,
        "created_document_count": 0,
        "skipped_document_count": 0,
        "migrated_chunk_count": 0,
        "embedding_count": 0,
        "source": "migration",
        "items": [],
    }

    assert postgresql_repository.inserted_documents == []
    assert postgresql_repository.inserted_chunks == []
    assert postgresql_repository.inserted_embeddings == []