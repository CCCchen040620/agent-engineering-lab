from week04.safe_file_reader import safe_read_text_file


def test_safe_read_text_file_existing_file():
    content = safe_read_text_file("data/company_docs/employee_handbook.txt")

    assert "员工手册" in content


def test_safe_read_text_file_missing_file_returns_empty_string():
    content = safe_read_text_file("data/company_docs/not_exists.txt")

    assert content == ""