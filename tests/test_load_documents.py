from week02.load_documents import load_documents


def test_load_documents_from_json_file():
    documents = load_documents("data/documents.json")

    assert len(documents) == 4
    assert documents[0]["title"] == "员工手册"
    assert documents[1]["is_indexed"] == False
    assert documents[2]["chunk_count"] == 5
    assert documents[3]["title"] == "培训资料"
    assert documents[3]["is_indexed"] == False