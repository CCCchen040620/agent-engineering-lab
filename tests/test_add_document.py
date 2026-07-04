from week02.add_document import build_document


def test_build_document():
    document = build_document("培训资料", "pdf", 3, False)

    assert document["title"] == "培训资料"
    assert document["file_type"] == "pdf"
    assert document["chunk_count"] == 3
    assert document["is_indexed"] == False