import pytest

from week02.add_document import build_document, parse_is_indexed


def test_build_document():
    document = build_document("培训资料", "pdf", 3, False)

    assert document["title"] == "培训资料"
    assert document["file_type"] == "pdf"
    assert document["chunk_count"] == 3
    assert document["is_indexed"] == False


def test_parse_is_indexed_yes():
    assert parse_is_indexed("yes") == True


def test_parse_is_indexed_no():
    assert parse_is_indexed("no") == False


def test_parse_is_indexed_rejects_other_text():
    with pytest.raises(ValueError):
        parse_is_indexed("maybe")


def test_build_document_rejects_empty_title():
    with pytest.raises(ValueError):
        build_document("", "pdf", 3, False)


def test_build_document_rejects_negative_chunk_count():
    with pytest.raises(ValueError):
        build_document("培训资料", "pdf", -1, False)