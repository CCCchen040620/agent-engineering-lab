from week03.read_text_file import read_text_file


def test_read_text_file_reads_content():
    content = read_text_file("data/company_docs/employee_handbook.txt")

    assert "员工手册" in content
    assert "弹性工作制" in content
    assert "安全培训" in content