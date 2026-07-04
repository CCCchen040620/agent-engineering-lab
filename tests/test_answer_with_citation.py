from week03.answer_with_citation import build_answer


def test_build_answer_with_citation():
    snippets = [
        {
            "title": "employee_handbook",
            "path": "data/company_docs/employee_handbook.txt",
            "text": "新员工入职后需要在 30 天内完成安全培训。",
        }
    ]

    answer = build_answer("安全培训", snippets)

    assert "新员工入职后需要在 30 天内完成安全培训。" in answer
    assert "来源：employee_handbook" in answer


def test_build_answer_refuses_when_no_snippet_found():
    answer = build_answer("股票期权", [])

    assert answer == "知识库中没有找到相关资料，暂时无法回答。"


def test_build_answer_uses_at_most_three_snippets():
    snippets = [
        {"title": "doc1", "path": "a.txt", "text": "片段1"},
        {"title": "doc2", "path": "b.txt", "text": "片段2"},
        {"title": "doc3", "path": "c.txt", "text": "片段3"},
        {"title": "doc4", "path": "d.txt", "text": "片段4"},
    ]

    answer = build_answer("测试", snippets)

    assert "片段1" in answer
    assert "片段2" in answer
    assert "片段3" in answer
    assert "片段4" not in answer


def test_build_answer_adds_citation_numbers():
    snippets = [
        {"title": "doc1", "path": "a.txt", "text": "片段1"},
        {"title": "doc2", "path": "b.txt", "text": "片段2"},
    ]

    answer = build_answer("测试", snippets)

    assert "[1] 片段1" in answer
    assert "[2] 片段2" in answer