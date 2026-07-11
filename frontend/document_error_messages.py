DOCUMENT_INDEXING_HELP_MESSAGE = (
    "文档索引失败：请确认 Ollama 已启动，并且 bge-m3:latest 模型可用。"
    "你可以在终端运行：ollama list"
)


def split_request_id_suffix(error_message: str) -> tuple[str, str]:
    suffix_start = error_message.find("（请求编号：")

    if suffix_start == -1:
        return error_message, ""

    return error_message[:suffix_start], error_message[suffix_start:]


def with_request_id_suffix(message: str, suffix: str) -> str:
    return message + suffix


def format_document_error_message(error_message: str) -> str:
    error_message, request_id_suffix = split_request_id_suffix(error_message)

    if "文档索引失败" in error_message:
        return with_request_id_suffix(
            DOCUMENT_INDEXING_HELP_MESSAGE,
            request_id_suffix,
        )

    if "文档标题过长" in error_message:
        return with_request_id_suffix(
            "文档标题过长：请把标题控制在 100 个字符以内。",
            request_id_suffix,
        )

    if "文档正文过长" in error_message:
        return with_request_id_suffix(
            "文档正文过长：请缩短内容，或拆成多份文档后再上传。",
            request_id_suffix,
        )

    if "上传文件过大" in error_message:
        return with_request_id_suffix(
            "上传文件过大：当前最大支持 1MB 的 txt 文件。",
            request_id_suffix,
        )

    if "请求过于频繁" in error_message:
        return with_request_id_suffix(
            "请求过于频繁：请稍等一会儿再重试。",
            request_id_suffix,
        )

    return with_request_id_suffix(error_message, request_id_suffix)
