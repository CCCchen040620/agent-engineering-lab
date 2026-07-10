from backend.services.conversation_summary_service import (
    build_conversation_summary,
    find_latest_user_question,
)


def test_find_latest_user_question_from_content():
    messages = [
        {
            "role": "user",
            "content": "新员工什么时候完成安全培训？",
        },
        {
            "role": "assistant",
            "content": "新员工需要在入职后 30 天内完成安全培训。",
        },
        {
            "role": "user",
            "content": "每天需要工作多久？",
        },
    ]

    result = find_latest_user_question(messages)

    assert result == "每天需要工作多久？"


def test_find_latest_user_question_prefers_metadata_question():
    messages = [
        {
            "role": "user",
            "content": "原始内容",
            "metadata": {
                "question": "每天需要工作多久？",
            },
        }
    ]

    result = find_latest_user_question(messages)

    assert result == "每天需要工作多久？"


def test_build_conversation_summary_with_question_and_citation():
    messages = [
        {
            "role": "user",
            "content": "每天需要工作多久？",
        },
        {
            "role": "assistant",
            "content": "员工每天需要完成 8 小时工作。",
            "metadata": {
                "citations": [
                    {
                        "title": "员工手册",
                        "text": "员工每天需要完成 8 小时工作。",
                        "path": "sqlite://1",
                    }
                ]
            },
        },
    ]

    result = build_conversation_summary(messages)

    assert result == "最近问题：每天需要工作多久？；最近引用文档：员工手册。"


def test_build_conversation_summary_with_question_only():
    messages = [
        {
            "role": "user",
            "content": "公司有没有股票期权？",
        },
        {
            "role": "assistant",
            "content": "知识库中没有找到相关资料，暂时无法回答。",
            "metadata": {
                "citations": []
            },
        },
    ]

    result = build_conversation_summary(messages)

    assert result == "最近问题：公司有没有股票期权？。"


def test_build_conversation_summary_returns_empty_string_without_useful_messages():
    messages = []

    result = build_conversation_summary(messages)

    assert result == ""