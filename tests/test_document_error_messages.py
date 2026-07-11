from frontend.document_error_messages import format_document_error_message


def test_format_document_error_message_explains_indexing_failure():
    message = format_document_error_message(
        "文档索引失败：本地 Embedding 模型不可用，请确认 Ollama 和 bge-m3 已启动。"
    )

    assert "请确认 Ollama 已启动" in message
    assert "bge-m3:latest" in message
    assert "ollama list" in message


def test_format_document_error_message_keeps_normal_errors():
    message = format_document_error_message("文档已存在。")

    assert message == "文档已存在。"
