from week10.migrate_one_sqlite_document_to_postgresql import (
    migrate_one_sqlite_document_to_postgresql,
)


class FakeSqliteRepository:
    def find_document_by_title(self, title: str):
        if title == "SQLite 迁移验收文档":
            return {
                "id": 1,
                "title": title,
                "file_type": "md",
                "chunk_count": 2,
                "is_indexed": True,
            }

        return None

    def list_chunks_by_document_id(self, document_id: int):
        return [
            {
                "id": 1,
                "document_id": document_id,
                "text": "SQLite 迁移测试片段一。",
            },
            {
                "id": 2,
                "document_id": document_id,
                "text": "SQLite 迁移测试片段二。",
            },
        ]


class FakePostgresqlRepository:
    def __init__(self):
        self.inserted_document = None
        self.inserted_chunks = []
        self.inserted_embeddings = []

    def find_document_by_title(self, title: str):
        return None

    def insert_document(self, title, file_type, chunk_count, is_indexed, source):
        self.inserted_document = {
            "id": 10,
            "title": title,
            "file_type": file_type,
            "chunk_count": chunk_count,
            "is_indexed": is_indexed,
            "source": source,
        }

        return self.inserted_document

    def insert_chunk(self, document_id: int, text: str, chunk_index: int):
        chunk = {
            "id": len(self.inserted_chunks) + 100,
            "document_id": document_id,
            "text": text,
            "chunk_index": chunk_index,
        }
        self.inserted_chunks.append(chunk)
        return chunk

    def upsert_embedding(self, chunk_id: int, embedding: list[float], model: str):
        item = {
            "chunk_id": chunk_id,
            "embedding": embedding,
            "model": model,
        }
        self.inserted_embeddings.append(item)
        return item


def fake_embedder(text: str, model: str):
    return [0.1, 0.2, 0.3]


def test_migrate_one_sqlite_document_to_postgresql():
    sqlite_repository = FakeSqliteRepository()
    postgresql_repository = FakePostgresqlRepository()

    result = migrate_one_sqlite_document_to_postgresql(
        sqlite_repository=sqlite_repository,
        postgresql_repository=postgresql_repository,
        title="SQLite 迁移验收文档",
        embedder=fake_embedder,
        embedding_model="fake-model",
    )

    assert result == {
        "created": True,
        "skipped": False,
        "reason": "",
        "title": "SQLite 迁移验收文档",
        "chunk_count": 2,
        "embedding_count": 2,
        "source": "migration",
    }

    assert postgresql_repository.inserted_document["source"] == "migration"
    assert len(postgresql_repository.inserted_chunks) == 2
    assert len(postgresql_repository.inserted_embeddings) == 2


def test_migrate_one_sqlite_document_returns_not_found_when_missing():
    sqlite_repository = FakeSqliteRepository()
    postgresql_repository = FakePostgresqlRepository()

    result = migrate_one_sqlite_document_to_postgresql(
        sqlite_repository=sqlite_repository,
        postgresql_repository=postgresql_repository,
        title="不存在的文档",
        embedder=fake_embedder,
        embedding_model="fake-model",
    )

    assert result == {
        "created": False,
        "skipped": True,
        "reason": "sqlite_document_not_found",
        "title": "不存在的文档",
        "chunk_count": 0,
        "embedding_count": 0,
        "source": "migration",
    }


class ExistingPostgresqlRepository(FakePostgresqlRepository):
    def find_document_by_title(self, title: str):
        return {
            "id": 10,
            "title": title,
            "file_type": "md",
            "chunk_count": 2,
            "is_indexed": True,
            "source": "migration",
        }


def test_migrate_one_sqlite_document_skips_existing_postgresql_document():
    sqlite_repository = FakeSqliteRepository()
    postgresql_repository = ExistingPostgresqlRepository()

    result = migrate_one_sqlite_document_to_postgresql(
        sqlite_repository=sqlite_repository,
        postgresql_repository=postgresql_repository,
        title="SQLite 迁移验收文档",
        embedder=fake_embedder,
        embedding_model="fake-model",
    )

    assert result == {
        "created": False,
        "skipped": True,
        "reason": "postgresql_document_already_exists",
        "title": "SQLite 迁移验收文档",
        "chunk_count": 0,
        "embedding_count": 0,
        "source": "migration",
    }

    assert postgresql_repository.inserted_document is None