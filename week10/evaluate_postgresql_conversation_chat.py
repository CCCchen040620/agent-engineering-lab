import requests

from backend.config import BACKEND_API_BASE_URL


DEFAULT_CONVERSATION_TITLE = "PostgreSQL 会话检索验收"
DEFAULT_FIRST_QUESTION = "员工每天需要工作多久？"
DEFAULT_SECOND_QUESTION = "这份文档里员工每天需要工作多久？"


def normalize_base_url(base_url: str) -> str:
    return base_url.rstrip("/")


def extract_error_detail(response) -> str:
    try:
        data = response.json()
    except Exception:
        return f"HTTP {response.status_code}"

    detail = data.get("detail")

    if isinstance(detail, str):
        return detail

    return f"HTTP {response.status_code}"


def read_json_response(response, expected_status_codes: set[int]) -> tuple[dict | list | None, str]:
    if response.status_code not in expected_status_codes:
        return None, extract_error_detail(response)

    return response.json(), ""


def create_conversation(
    http_client,
    base_url: str,
    title: str,
) -> tuple[dict | None, str]:
    try:
        response = http_client.post(
            normalize_base_url(base_url) + "/api/v1/conversations",
            json={"title": title},
            timeout=30,
        )
    except requests.RequestException as error:
        return None, str(error)

    return read_json_response(response, {201})


def chat_with_postgresql_conversation(
    http_client,
    base_url: str,
    conversation_id: int,
    question: str,
    top_k: int,
    mode: str,
    min_score: float,
    timeout_seconds: float,
) -> tuple[dict | None, str]:
    try:
        response = http_client.post(
            normalize_base_url(base_url)
            + f"/api/v1/langgraph-agent/conversations/{conversation_id}/chat",
            params={
                "retriever_backend": "postgresql",
                "top_k": top_k,
                "mode": mode,
                "min_score": min_score,
                "timeout_seconds": timeout_seconds,
            },
            json={"question": question},
            timeout=300,
        )
    except requests.RequestException as error:
        return None, str(error)

    return read_json_response(response, {200})


def list_conversation_messages(
    http_client,
    base_url: str,
    conversation_id: int,
) -> tuple[list[dict] | None, str]:
    try:
        response = http_client.get(
            normalize_base_url(base_url)
            + f"/api/v1/conversations/{conversation_id}/messages",
            timeout=30,
        )
    except requests.RequestException as error:
        return None, str(error)

    data, error = read_json_response(response, {200})

    if data is None:
        return None, error

    return data, ""


def is_postgresql_citation(citation: dict) -> bool:
    return citation.get("path", "").startswith("postgresql://chunk/")


def has_postgresql_citation(response: dict) -> bool:
    for citation in response.get("citations", []):
        if is_postgresql_citation(citation):
            return True

    return False


def get_top_citation_title(response: dict) -> str:
    citations = response.get("citations", [])

    if citations == []:
        return ""

    return citations[0].get("title", "")


def response_uses_conversation_context(response: dict, expected_title: str) -> bool:
    if expected_title == "":
        return False

    if response.get("context_document_title", "") == expected_title:
        return True

    contextual_question = response.get("contextual_question", "")

    return expected_title in contextual_question


def build_failed_result(reason: str, **extra) -> dict:
    return {
        "passed": False,
        "failure_reason": reason,
        **extra,
    }


def evaluate_postgresql_conversation_chat_flow(
    http_client=requests,
    base_url: str = BACKEND_API_BASE_URL,
    conversation_title: str = DEFAULT_CONVERSATION_TITLE,
    first_question: str = DEFAULT_FIRST_QUESTION,
    second_question: str = DEFAULT_SECOND_QUESTION,
    top_k: int = 3,
    mode: str = "precomputed_embedding",
    min_score: float = 0.6,
    timeout_seconds: float = 30,
) -> dict:
    conversation, error = create_conversation(
        http_client=http_client,
        base_url=base_url,
        title=conversation_title,
    )

    if error != "":
        return build_failed_result(
            "create_conversation_failed",
            error=error,
        )

    conversation_id = conversation["id"]

    first_response, error = chat_with_postgresql_conversation(
        http_client=http_client,
        base_url=base_url,
        conversation_id=conversation_id,
        question=first_question,
        top_k=top_k,
        mode=mode,
        min_score=min_score,
        timeout_seconds=timeout_seconds,
    )

    if error != "":
        return build_failed_result(
            "first_chat_failed",
            conversation_id=conversation_id,
            error=error,
        )

    messages_after_first, error = list_conversation_messages(
        http_client=http_client,
        base_url=base_url,
        conversation_id=conversation_id,
    )

    if error != "":
        return build_failed_result(
            "list_messages_after_first_failed",
            conversation_id=conversation_id,
            first_response=first_response,
            error=error,
        )

    expected_context_title = get_top_citation_title(first_response)

    second_response, error = chat_with_postgresql_conversation(
        http_client=http_client,
        base_url=base_url,
        conversation_id=conversation_id,
        question=second_question,
        top_k=top_k,
        mode=mode,
        min_score=min_score,
        timeout_seconds=timeout_seconds,
    )

    if error != "":
        return build_failed_result(
            "second_chat_failed",
            conversation_id=conversation_id,
            first_response=first_response,
            messages_after_first_count=len(messages_after_first),
            error=error,
        )

    messages_after_second, error = list_conversation_messages(
        http_client=http_client,
        base_url=base_url,
        conversation_id=conversation_id,
    )

    if error != "":
        return build_failed_result(
            "list_messages_after_second_failed",
            conversation_id=conversation_id,
            first_response=first_response,
            second_response=second_response,
            messages_after_first_count=len(messages_after_first),
            error=error,
        )

    first_has_postgresql_citation = has_postgresql_citation(first_response)
    first_messages_saved = len(messages_after_first) >= 2
    second_used_conversation_context = response_uses_conversation_context(
        second_response,
        expected_context_title,
    )
    second_messages_saved = len(messages_after_second) >= 4

    passed = (
        first_has_postgresql_citation
        and first_messages_saved
        and second_used_conversation_context
        and second_messages_saved
    )

    return {
        "passed": passed,
        "failure_reason": "" if passed else "postgresql_conversation_chat_flow_failed",
        "conversation_id": conversation_id,
        "conversation_title": conversation["title"],
        "retriever_backend": "postgresql",
        "mode": mode,
        "top_k": top_k,
        "min_score": min_score,
        "first_question": first_question,
        "second_question": second_question,
        "expected_context_title": expected_context_title,
        "first_has_postgresql_citation": first_has_postgresql_citation,
        "first_citation_count": len(first_response.get("citations", [])),
        "first_messages_saved": first_messages_saved,
        "messages_after_first_count": len(messages_after_first),
        "second_used_conversation_context": second_used_conversation_context,
        "second_context_document_title": second_response.get(
            "context_document_title",
            "",
        ),
        "second_contextual_question": second_response.get(
            "contextual_question",
            "",
        ),
        "second_messages_saved": second_messages_saved,
        "messages_after_second_count": len(messages_after_second),
        "first_response": first_response,
        "second_response": second_response,
    }


def print_evaluation_result(result: dict) -> None:
    print("PostgreSQL 会话保存 Agent 验收完成。")
    print("是否通过：", result["passed"])

    if result.get("failure_reason", "") != "":
        print("失败原因：", result["failure_reason"])

    if result.get("error", "") != "":
        print("错误信息：", result["error"])

    print("会话 ID：", result.get("conversation_id", ""))
    print("检索后端：", result.get("retriever_backend", "postgresql"))
    print("检索模式：", result.get("mode", ""))
    print("top_k：", result.get("top_k", ""))
    print("min_score：", result.get("min_score", ""))
    print("-" * 50)
    print("第一轮问题：", result.get("first_question", ""))
    print("第一轮是否有 PostgreSQL 引用：", result.get("first_has_postgresql_citation", False))
    print("第一轮引用数量：", result.get("first_citation_count", 0))
    print("第一轮后消息数量：", result.get("messages_after_first_count", 0))
    print("-" * 50)
    print("第二轮问题：", result.get("second_question", ""))
    print("期望上下文文档：", result.get("expected_context_title", ""))
    print("第二轮上下文文档：", result.get("second_context_document_title", ""))
    print("第二轮上下文问题：", result.get("second_contextual_question", ""))
    print("第二轮是否使用会话上下文：", result.get("second_used_conversation_context", False))
    print("第二轮后消息数量：", result.get("messages_after_second_count", 0))


def main():
    result = evaluate_postgresql_conversation_chat_flow()
    print_evaluation_result(result)

    if result["passed"] is not True:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
