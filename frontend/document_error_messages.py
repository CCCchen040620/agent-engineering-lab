DOCUMENT_INDEXING_HELP_MESSAGE = (
    "文档索引失败：请确认 Ollama 已启动，并且 bge-m3:latest 模型可用。"
    "你可以在终端运行：ollama list"
)


def format_document_error_message(error_message: str) -> str:
    if "文档索引失败" in error_message:
        return DOCUMENT_INDEXING_HELP_MESSAGE

    return error_message
