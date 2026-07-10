from week07.simple_vector_search import (
    build_term_frequency,
    cosine_similarity,
)


def find_latest_cited_document_title(messages: list[dict]) -> str:
    for message in reversed(messages):
        metadata = message.get("metadata", {})
        citations = metadata.get("citations", [])

        if citations != []:
            return citations[0]["title"]

    return ""


def find_latest_cited_document_title_from_summary(summary: str) -> str:
    marker = "最近引用文档："

    if marker not in summary:
        return ""

    after_marker = summary.split(marker, 1)[1]

    if "。" in after_marker:
        return after_marker.split("。", 1)[0].strip()

    return after_marker.strip()


def build_contextual_question(
    question: str,
    messages: list[dict],
    conversation_summary: str = "",
) -> str:
    latest_cited_document_title = find_latest_cited_document_title(messages)

    if latest_cited_document_title == "":
        latest_cited_document_title = find_latest_cited_document_title_from_summary(
            conversation_summary
        )

    if latest_cited_document_title == "":
        return question

    return latest_cited_document_title + " " + question


def calculate_question_similarity(question: str, text: str) -> float:
    question_vector = build_term_frequency(question)
    text_vector = build_term_frequency(text)

    return cosine_similarity(question_vector, text_vector)


def is_contextual_context_valid(
    question: str,
    context_document_title: str,
    snippets: list[dict],
) -> bool:
    if context_document_title == "":
        return False

    for snippet in snippets:
        if snippet["title"] != context_document_title:
            continue

        question_similarity = calculate_question_similarity(
            question=question,
            text=snippet["text"],
        )

        if question_similarity >= 0.3:
            return True

    return False

    
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