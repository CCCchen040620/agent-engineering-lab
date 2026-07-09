from backend.services.conversation_context_service import (
    infer_document_title_from_messages,
)


def test_infer_document_title_from_messages():
    messages = [
        {
            "role": "assistant",
            "content": "员工手册 的片段如下：\n[1] 员工每天需要完成 8 小时工作。",
        }
    ]

    result = infer_document_title_from_messages(messages)

    assert result == "员工手册"


def test_infer_document_title_from_messages_uses_latest_document():
    messages = [
        {
            "role": "assistant",
            "content": "员工手册 的片段如下：\n[1] 员工每天需要完成 8 小时工作。",
        },
        {
            "role": "assistant",
            "content": "请假制度 的片段如下：\n[1] 员工请假需要提前申请。",
        },
    ]

    result = infer_document_title_from_messages(messages)

    assert result == "请假制度"


def test_infer_document_title_from_messages_returns_empty_string_when_not_found():
    messages = [
        {
            "role": "user",
            "content": "公司有没有股票期权？",
        },
        {
            "role": "assistant",
            "content": "知识库中没有找到相关资料，暂时无法回答。",
        },
    ]

    result = infer_document_title_from_messages(messages)

    assert result == ""


def test_infer_document_title_from_messages_uses_latest_user_question():
    messages = [
        {
            "role": "user",
            "content": "查看员工手册的片段",
        }
    ]

    result = infer_document_title_from_messages(messages)

    assert result == "员工手册"


def test_infer_document_title_from_messages_uses_latest_user_document():
    messages = [
        {
            "role": "user",
            "content": "查看员工手册的片段",
        },
        {
            "role": "user",
            "content": "查看请假制度的片段",
        },
    ]

    result = infer_document_title_from_messages(messages)

    assert result == "请假制度"


def test_infer_document_title_from_messages_uses_metadata_citation():
    messages = [
        {
            "role": "assistant",
            "content": "这里的文本格式不重要。",
            "metadata": {
                "citations": [
                    {
                        "title": "员工手册",
                        "text": "新员工入职后需要在 30 天内完成安全培训。",
                        "path": "sqlite://1",
                    }
                ]
            },
        }
    ]

    result = infer_document_title_from_messages(messages)

    assert result == "员工手册"


def test_infer_document_title_from_messages_skips_empty_citations():
    messages = [
        {
            "role": "assistant",
            "content": "员工手册 的片段如下：\n[1] 新员工入职后需要在 30 天内完成安全培训。",
            "metadata": {
                "citations": [
                    {
                        "title": "员工手册",
                        "text": "新员工入职后需要在 30 天内完成安全培训。",
                        "path": "sqlite://1",
                    }
                ]
            },
        },
        {
            "role": "assistant",
            "content": "知识库中没有找到相关资料，暂时无法回答。",
            "metadata": {
                "citations": []
            },
        },
    ]

    result = infer_document_title_from_messages(messages)

    assert result == "员工手册"