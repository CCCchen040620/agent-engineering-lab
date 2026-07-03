from week01.hello_agent import build_greeting


def test_build_greeting_uses_name_and_goal() -> None:
    result = build_greeting("小明", "开发知识库 Agent")

    assert "小明" in result
    assert "开发知识库 Agent" in result


def test_build_greeting_handles_empty_input() -> None:
    result = build_greeting("   ", "")

    assert "同学" in result
    assert "学习 Agent 开发" in result
