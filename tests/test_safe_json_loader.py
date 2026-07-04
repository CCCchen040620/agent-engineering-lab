from week04.safe_json_loader import safe_load_json_list


def test_safe_load_json_list_existing_list_file(tmp_path):
    file_path = tmp_path / "documents.json"
    file_path.write_text('[{"title": "测试文档"}]', encoding="utf-8")

    data = safe_load_json_list(file_path)

    assert data == [{"title": "测试文档"}]


def test_safe_load_json_list_missing_file_returns_empty_list(tmp_path):
    file_path = tmp_path / "missing.json"

    data = safe_load_json_list(file_path)

    assert data == []


def test_safe_load_json_list_invalid_json_returns_empty_list(tmp_path):
    file_path = tmp_path / "broken.json"
    file_path.write_text('[{"title": "测试文档"}', encoding="utf-8")

    data = safe_load_json_list(file_path)

    assert data == []


def test_safe_load_json_list_non_list_json_returns_empty_list(tmp_path):
    file_path = tmp_path / "single_document.json"
    file_path.write_text('{"title": "测试文档"}', encoding="utf-8")

    data = safe_load_json_list(file_path)

    assert data == []