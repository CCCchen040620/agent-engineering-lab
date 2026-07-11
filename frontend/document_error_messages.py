DOCUMENT_INDEXING_HELP_MESSAGE = (
    "文档索引失败：请确认 Ollama 已启动，并且 bge-m3:latest 模型可用。"
    "你可以在终端运行：ollama list"
)


def format_document_error_message(error_message: str) -> str:
    if "文档索引失败" in error_message:
        return DOCUMENT_INDEXING_HELP_MESSAGE

    if "文档标题过长" in error_message:
        return "文档标题过长：请把标题控制在 100 个字符以内。"

    if "文档正文过长" in error_message:
        return "文档正文过长：请缩短内容，或拆成多份文档后再上传。"

    if "上传文件过大" in error_message:
        return "上传文件过大：当前最大支持 1MB 的 txt 文件。"

    if "请求过于频繁" in error_message:
        return "请求过于频繁：请稍等一会儿再重试。"

    return error_message
