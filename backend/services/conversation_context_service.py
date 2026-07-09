def infer_document_title_from_messages(messages: list[dict]) -> str:
    for message in reversed(messages):
        content = message["content"]

        answer_marker = " 的片段如下"

        if answer_marker in content:
            return content.split(answer_marker)[0].strip()

        question_prefix = "查看"
        question_suffix = "的片段"

        if content.startswith(question_prefix) and question_suffix in content:
            without_prefix = content.removeprefix(question_prefix)
            return without_prefix.split(question_suffix)[0].strip()

    return ""