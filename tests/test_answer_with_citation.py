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