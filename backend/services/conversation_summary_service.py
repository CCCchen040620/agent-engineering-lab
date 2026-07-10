from backend.services.conversation_context_service import (
    find_latest_cited_document_title,
)


def find_latest_user_question(messages: list[dict]) -> str:
    for message in reversed(messages):
        if message.get("role") != "user":
            continue

        metadata = message.get("metadata", {})
        question = metadata.get("question", "")

        if question != "":
            return question

        return message.get("content", "")

    return ""


def build_conversation_summary(messages: list[dict]) -> str:
    latest_user_question = find_latest_user_question(messages)
    latest_cited_document_title = find_latest_cited_document_title(messages)

    summary_parts = []

    if latest_user_question != "":
        summary_parts.append(f"最近问题：{latest_user_question}")

    if latest_cited_document_title != "":
        summary_parts.append(f"最近引用文档：{latest_cited_document_title}")

    if summary_parts == []:
        return ""

    return "；".join(summary_parts) + "。"