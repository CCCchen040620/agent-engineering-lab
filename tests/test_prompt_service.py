from backend.services.prompt_service import build_rag_prompt


def test_build_rag_prompt_contains_question():
    snippets = [
        {
            "title": "员工手册",
            "text": "新员工入职后需要在 30 天内完成安全培训。",
            "path": "sqlite://1",
        }
    ]

    prompt = build_rag_prompt("新员工什么时候完成安全培训？", snippets)

    assert "新员工什么时候完成安全培训？" in prompt


def test_build_rag_prompt_contains_snippet_text():
    snippets = [
        {
            "title": "员工手册",
            "text": "新员工入职后需要在 30 天内完成安全培训。",
            "path": "sqlite://1",
        }
    ]

    prompt = build_rag_prompt("新员工什么时候完成安全培训？", snippets)

    assert "新员工入职后需要在 30 天内完成安全培训。" in prompt


def test_build_rag_prompt_tells_model_to_refuse_unknown_answer():
    prompt = build_rag_prompt("公司有没有股票期权？", [])

    assert "知识库中没有找到相关资料，暂时无法回答" in prompt