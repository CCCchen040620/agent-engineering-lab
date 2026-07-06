from backend.services.document_indexing_service import (
    create_document_with_chunks_and_embeddings,
    create_document_with_chunks,
    split_text_into_chunks,
    split_long_text,
)
from backend.services.sqlite_document_repository import (
    create_connection,
    list_chunks_by_document_id,
)
from backend.services.sqlite_embedding_repository import (
    find_chunk_embedding_by_chunk_id,
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


def test_split_text_into_chunks_supports_question_and_exclamation_marks():
    chunks = split_text_into_chunks(
        "员工可以远程办公吗？可以！需要提前申请。"
    )

    assert chunks == [
        "员工可以远程办公吗。",
        "可以。",
        "需要提前申请。",
    ]


def test_split_text_into_chunks_supports_new_lines():
    chunks = split_text_into_chunks(
        "第一行内容\n第二行内容"
    )

    assert chunks == [
        "第一行内容。",
        "第二行内容。",
    ]


def test_split_long_text_by_max_chunk_size():
    chunks = split_long_text("abcdefghij", max_chunk_size=4)

    assert chunks == [
        "abcd",
        "efgh",
        "ij",
    ]


def test_split_text_into_chunks_splits_long_chunk():
    chunks = split_text_into_chunks(
        "abcdefghij",
        max_chunk_size=4,
    )

    assert chunks == [
        "abcd",
        "efgh",
        "ij。",
    ]


def test_create_document_with_chunks_returns_none_when_no_valid_chunks(tmp_path):
    database_path = tmp_path / "test.db"
    connection = create_connection(str(database_path))

    document = create_document_with_chunks(
        connection,
        title="空内容制度",
        file_type="md",
        content="。。。\n   ！！！？？？",
    )

    connection.close()

    assert document is None


def test_create_document_with_chunks_and_embeddings(tmp_path):
    database_path = tmp_path / "test.db"
    connection = create_connection(str(database_path))

    def fake_embedder(text: str) -> list[float]:
        return [float(len(text)), 1.0]

    document = create_document_with_chunks_and_embeddings(
        connection,
        title="远程办公制度",
        file_type="md",
        content="员工可以远程办公。远程办公需要提前申请。",
        embedder=fake_embedder,
    )

    chunks = list_chunks_by_document_id(connection, document["id"])

    first_embedding = find_chunk_embedding_by_chunk_id(
        connection,
        chunks[0]["id"],
    )

    second_embedding = find_chunk_embedding_by_chunk_id(
        connection,
        chunks[1]["id"],
    )

    connection.close()

    assert document["chunk_count"] == 2
    assert len(chunks) == 2
    assert first_embedding["embedding"] == [float(len(chunks[0]["text"])), 1.0]
    assert second_embedding["embedding"] == [float(len(chunks[1]["text"])), 1.0]