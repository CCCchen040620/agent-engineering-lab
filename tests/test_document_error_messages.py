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


def test_format_document_error_message_explains_too_long_title():
    message = format_document_error_message("文档标题过长，最多支持 100 个字符。")

    assert "100 个字符以内" in message


def test_format_document_error_message_explains_too_long_content():
    message = format_document_error_message("文档正文过长，最多支持 20000 个字符。")

    assert "拆成多份文档" in message


def test_format_document_error_message_explains_too_large_file():
    message = format_document_error_message("上传文件过大，最大支持 1048576 字节。")

    assert "1MB" in message


def test_format_document_error_message_explains_rate_limit():
    message = format_document_error_message("请求过于频繁，请稍后再试。")

    assert "稍等一会儿" in message


def test_format_document_error_message_keeps_request_id_suffix():
    message = format_document_error_message(
        "请求过于频繁，请稍后再试。（请求编号：rate-limit-request）"
    )

    assert "稍等一会儿" in message
    assert "请求编号：rate-limit-request" in message
