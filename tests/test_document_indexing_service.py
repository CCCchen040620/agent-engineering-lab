from backend.services.document_indexing_service import (
    create_document_with_chunks,
    split_text_into_chunks,
)
from backend.services.sqlite_document_repository import (
    create_connection,
    list_chunks_by_document_id,
)


def test_split_text_into_chunks():
    chunks = split_text_into_chunks(
        "员工每周可以申请一天远程办公。远程办公需要提前提交申请。"
    )

    assert chunks == [
        "员工每周可以申请一天远程办公。",
        "远程办公需要提前提交申请。",
    ]


def test_create_document_with_chunks(tmp_path):
    database_path = tmp_path / "test.db"
    connection = create_connection(str(database_path))

    document = create_document_with_chunks(
        connection,
        title="远程办公制度",
        file_type="md",
        content="员工每周可以申请一天远程办公。远程办公需要提前提交申请。",
    )

    chunks = list_chunks_by_document_id(connection, document["id"])

    connection.close()

    assert document["title"] == "远程办公制度"
    assert document["chunk_count"] == 2
    assert document["is_indexed"] == True
    assert len(chunks) == 2


def test_create_document_with_chunks_returns_none_for_duplicate_title(tmp_path):
    database_path = tmp_path / "test.db"
    connection = create_connection(str(database_path))

    first_document = create_document_with_chunks(
        connection,
        title="远程办公制度",
        file_type="md",
        content="员工每周可以申请一天远程办公。",
    )

    second_document = create_document_with_chunks(
        connection,
        title="远程办公制度",
        file_type="md",
        content="重复文档。",
    )

    chunks = list_chunks_by_document_id(connection, first_document["id"])

    connection.close()

    assert second_document is None
    assert len(chunks) == 1