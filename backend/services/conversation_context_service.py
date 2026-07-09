def find_latest_cited_document_title(messages: list[dict]) -> str:
    for message in reversed(messages):
        metadata = message.get("metadata", {})
        citations = metadata.get("citations", [])

        if citations != []:
            return citations[0]["title"]

    return ""


def infer_document_title_from_messages(messages: list[dict]) -> str:
    latest_cited_document_title = find_latest_cited_document_title(messages)

    if latest_cited_document_title != "":
        return latest_cited_document_title

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