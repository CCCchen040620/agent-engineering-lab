from backend.services.postgresql_document_repository import (
    find_document_by_title_from_postgresql,
    insert_chunk_to_postgresql,
    insert_document_to_postgresql,
    list_chunks_by_document_from_postgresql,
    list_documents_from_postgresql,
    row_to_chunk,
    row_to_document,
    update_document_source_by_title_from_postgresql,
    delete_documents_by_source_from_postgresql,
)


class FakeCursor:
    def __init__(self):
        self.sql = ""
        self.params = None
        self.rows = []
        self.row = None

    def execute(self, sql: str, params=None):
        self.sql = sql
        self.params = params

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return self.row

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass


class FakeConnection:
    def __init__(self):
        self.cursor_instance = FakeCursor()
        self.committed = False

    def cursor(self):
        return self.cursor_instance

    def commit(self):
        self.committed = True


def test_row_to_document():
    row = (1, "员工手册", "md", 12, True)

    document = row_to_document(row)

    assert document == {
        "id": 1,
        "title": "员工手册",
        "file_type": "md",
        "chunk_count": 12,
        "is_indexed": True,
        "source": "production",
    }


def test_row_to_document_defaults_source_for_legacy_rows():
    row = (1, "鍛樺伐鎵嬪唽", "md", 12, True)

    document = row_to_document(row)

    assert document["source"] == "production"


def test_list_documents_from_postgresql():
    connection = FakeConnection()
    connection.cursor_instance.rows = [
        (1, "员工手册", "md", 12, True),
        (2, "报销制度", "pdf", 8, False),
    ]

    documents = list_documents_from_postgresql(connection)

    assert len(documents) == 2
    assert documents[0]["title"] == "员工手册"
    assert documents[0]["source"] == "production"
    assert documents[1]["is_indexed"] is False
    assert documents[1]["source"] == "production"
    assert "SELECT id, title, file_type, chunk_count, is_indexed, source" in (
        connection.cursor_instance.sql
    )


def test_list_documents_from_postgresql_filters_by_source():
    connection = FakeConnection()
    connection.cursor_instance.rows = [
        (1, "Evaluation Doc", "md", 2, True, "evaluation"),
    ]

    documents = list_documents_from_postgresql(
        connection,
        source="evaluation",
    )

    assert len(documents) == 1
    assert documents[0]["title"] == "Evaluation Doc"
    assert documents[0]["source"] == "evaluation"
    assert connection.cursor_instance.params == ("evaluation",)
    assert "WHERE source = %s" in connection.cursor_instance.sql


def test_insert_document_to_postgresql():
    connection = FakeConnection()
    connection.cursor_instance.row = (1, "员工手册", "md", 12, True)

    connection.cursor_instance.row = (*connection.cursor_instance.row, "production")

    document = insert_document_to_postgresql(
        connection,
        title="员工手册",
        file_type="md",
        chunk_count=12,
        is_indexed=True,
    )

    assert document["id"] == 1
    assert document["title"] == "员工手册"
    assert connection.cursor_instance.params == (
        "员工手册",
        "md",
        12,
        True,
        "production",
    )
    assert "INSERT INTO documents" in connection.cursor_instance.sql
    assert "RETURNING id, title, file_type, chunk_count, is_indexed, source" in (
        connection.cursor_instance.sql
    )
    assert connection.committed is True


def test_row_to_chunk():
    row = (1, 10, "员工每天需要完成 8 小时工作。", 0)

    chunk = row_to_chunk(row)

    assert chunk == {
        "id": 1,
        "document_id": 10,
        "text": "员工每天需要完成 8 小时工作。",
        "chunk_index": 0,
    }


def test_insert_chunk_to_postgresql():
    connection = FakeConnection()
    connection.cursor_instance.row = (
        1,
        10,
        "员工每天需要完成 8 小时工作。",
        0,
    )

    chunk = insert_chunk_to_postgresql(
        connection,
        document_id=10,
        text="员工每天需要完成 8 小时工作。",
        chunk_index=0,
    )

    assert chunk["id"] == 1
    assert chunk["document_id"] == 10
    assert chunk["text"] == "员工每天需要完成 8 小时工作。"
    assert chunk["chunk_index"] == 0
    assert connection.cursor_instance.params == (
        10,
        "员工每天需要完成 8 小时工作。",
        0,
    )
    assert "INSERT INTO chunks" in connection.cursor_instance.sql
    assert "RETURNING id, document_id, text, chunk_index" in (
        connection.cursor_instance.sql
    )
    assert connection.committed is True


def test_list_chunks_by_document_from_postgresql():
    connection = FakeConnection()
    connection.cursor_instance.rows = [
        (1, 10, "片段1", 0),
        (2, 10, "片段2", 1),
    ]

    chunks = list_chunks_by_document_from_postgresql(
        connection,
        document_id=10,
    )

    assert len(chunks) == 2
    assert chunks[0]["text"] == "片段1"
    assert chunks[1]["chunk_index"] == 1
    assert connection.cursor_instance.params == (10,)
    assert "FROM chunks" in connection.cursor_instance.sql
    assert "WHERE document_id = %s" in connection.cursor_instance.sql
    assert "ORDER BY chunk_index, id" in connection.cursor_instance.sql


def test_find_document_by_title_from_postgresql():
    connection = FakeConnection()
    connection.cursor_instance.row = (1, "员工手册", "md", 12, True)

    connection.cursor_instance.row = (*connection.cursor_instance.row, "production")

    document = find_document_by_title_from_postgresql(
        connection,
        title="员工手册",
    )

    assert document == {
        "id": 1,
        "title": "员工手册",
        "file_type": "md",
        "chunk_count": 12,
        "is_indexed": True,
        "source": "production",
    }
    assert connection.cursor_instance.params == ("员工手册",)
    assert "FROM documents" in connection.cursor_instance.sql
    assert "WHERE title = %s" in connection.cursor_instance.sql


def test_update_document_source_by_title_from_postgresql():
    connection = FakeConnection()
    connection.cursor_instance.row = (
        1,
        "PostgreSQL Agent 端到端验收文档",
        "md",
        2,
        True,
        "evaluation",
    )

    document = update_document_source_by_title_from_postgresql(
        connection,
        title="PostgreSQL Agent 端到端验收文档",
        source="evaluation",
    )

    assert document == {
        "id": 1,
        "title": "PostgreSQL Agent 端到端验收文档",
        "file_type": "md",
        "chunk_count": 2,
        "is_indexed": True,
        "source": "evaluation",
    }
    assert connection.cursor_instance.params == (
        "evaluation",
        "PostgreSQL Agent 端到端验收文档",
    )
    assert "UPDATE documents" in connection.cursor_instance.sql
    assert "SET source = %s" in connection.cursor_instance.sql
    assert "WHERE title = %s" in connection.cursor_instance.sql
    assert connection.committed is True


def test_update_document_source_by_title_from_postgresql_returns_none_when_not_found():
    connection = FakeConnection()
    connection.cursor_instance.row = None

    document = update_document_source_by_title_from_postgresql(
        connection,
        title="不存在的文档",
        source="evaluation",
    )

    assert document is None
    assert connection.committed is True


def test_find_document_by_title_from_postgresql_returns_none_when_not_found():
    connection = FakeConnection()
    connection.cursor_instance.row = None

    document = find_document_by_title_from_postgresql(
        connection,
        title="不存在的文档",
    )

    assert document is None
    assert connection.cursor_instance.params == ("不存在的文档",)


def test_delete_documents_by_source_from_postgresql():
    connection = FakeConnection()
    connection.cursor_instance.rows = [
        (1,),
        (2,),
    ]

    deleted_count = delete_documents_by_source_from_postgresql(
        connection,
        source="evaluation",
    )

    assert deleted_count == 2
    assert connection.cursor_instance.params == ("evaluation",)
    assert "DELETE FROM documents" in connection.cursor_instance.sql
    assert "WHERE source = %s" in connection.cursor_instance.sql
    assert connection.committed is True