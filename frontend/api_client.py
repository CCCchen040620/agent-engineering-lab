"""Small HTTP helpers used by Streamlit pages."""

import json

import requests


def get_system_status_api(base_url: str) -> tuple[dict | None, str | None]:
    """Get backend, database, Ollama, and model status."""
    try:
        response = requests.get(
            base_url + "/api/v1/system/status",
            timeout=30,
        )
    except requests.RequestException:
        return None, "后端服务暂时不可用，请确认 FastAPI 已启动。"

    if response.status_code == 200:
        return response.json(), None

    return None, get_error_detail(response)


def chat_with_llm_api(
    base_url: str,
    question: str,
    top_k: int,
    mode: str,
    min_score: float,
) -> tuple[dict | None, str | None]:
    """Ask the FastAPI LLM RAG endpoint and return data or an error message."""
    try:
        response = requests.post(
            base_url + "/api/v1/db/chat/llm",
            params={
                "top_k": top_k,
                "mode": mode,
                "min_score": min_score,
            },
            json={"question": question},
            timeout=300,
        )
    except requests.RequestException:
        return None, "后端服务暂时不可用，请确认 FastAPI 已启动。"

    if response.status_code == 200:
        return response.json(), None

    return None, get_error_detail(response)


def chat_with_agent_api(
    base_url: str,
    question: str,
    top_k: int,
    mode: str,
    min_score: float,
) -> tuple[dict | None, str | None]:
    """Ask the FastAPI Simple Agent endpoint and return data or an error."""
    try:
        response = requests.post(
            base_url + "/api/v1/agent/chat",
            params={
                "top_k": top_k,
                "mode": mode,
                "min_score": min_score,
            },
            json={"question": question},
            timeout=300,
        )
    except requests.RequestException:
        return None, "后端服务暂时不可用，请确认 FastAPI 已启动。"

    if response.status_code == 200:
        return response.json(), None

    return None, get_error_detail(response)


def chat_with_langgraph_agent_api(
    base_url: str,
    question: str,
    top_k: int,
    mode: str,
    min_score: float,
    timeout_seconds: int,
) -> tuple[dict | None, str | None]:
    """Ask the FastAPI LangGraph Agent endpoint and return data or an error."""
    try:
        response = requests.post(
            base_url + "/api/v1/langgraph-agent/chat",
            params={
                "top_k": top_k,
                "mode": mode,
                "min_score": min_score,
                "timeout_seconds": timeout_seconds,
            },
            json={"question": question},
            timeout=300,
        )
    except requests.RequestException:
        return None, "后端服务暂时不可用，请确认 FastAPI 已启动。"

    if response.status_code == 200:
        return response.json(), None

    return None, get_error_detail(response)


def stream_langgraph_agent_api(
    base_url: str,
    question: str,
    top_k: int,
    mode: str,
    min_score: float,
    timeout_seconds: int,
):
    """Stream LangGraph Agent SSE events from FastAPI."""
    try:
        response = requests.post(
            base_url + "/api/v1/langgraph-agent/chat/stream",
            params={
                "top_k": top_k,
                "mode": mode,
                "min_score": min_score,
                "timeout_seconds": timeout_seconds,
            },
            json={"question": question},
            timeout=300,
            stream=True,
        )
    except requests.RequestException:
        yield {
            "type": "error",
            "message": "后端服务暂时不可用，请确认 FastAPI 已启动。",
        }
        return

    if response.status_code != 200:
        yield {
            "type": "error",
            "message": get_error_detail(response),
        }
        return

    for line in response.iter_lines(decode_unicode=True):
        if line == "":
            continue

        event = parse_sse_event_line(line)

        if event is not None:
            yield event

            
def chat_with_langgraph_agent_conversation_api(
    base_url: str,
    conversation_id: int,
    question: str,
    top_k: int,
    mode: str,
    min_score: float,
    timeout_seconds: int,
) -> tuple[dict | None, str | None]:
    """Ask the LangGraph Agent endpoint and save messages to a conversation."""
    try:
        response = requests.post(
            base_url
            + f"/api/v1/langgraph-agent/conversations/{conversation_id}/chat",
            params={
                "top_k": top_k,
                "mode": mode,
                "min_score": min_score,
                "timeout_seconds": timeout_seconds,
            },
            json={"question": question},
            timeout=300,
        )
    except requests.RequestException:
        return None, "后端服务暂时不可用，请确认 FastAPI 已启动。"

    if response.status_code == 200:
        return response.json(), None

    return None, get_error_detail(response)
    

def get_conversation_api(
    base_url: str,
    conversation_id: int,
) -> tuple[dict | None, str | None]:
    """Get one conversation by id."""
    try:
        response = requests.get(
            base_url + f"/api/v1/conversations/{conversation_id}",
            timeout=30,
        )
    except requests.RequestException:
        return None, "后端服务暂时不可用，请确认 FastAPI 已启动。"

    if response.status_code == 200:
        return response.json(), None

    return None, get_error_detail(response)
    
       
def submit_feedback_api(
    base_url: str,
    question: str,
    answer: str,
    rating: str,
) -> tuple[dict | None, str | None]:
    """Submit answer feedback through the FastAPI feedback endpoint."""
    try:
        response = requests.post(
            base_url + "/api/v1/feedback",
            json={
                "question": question,
                "answer": answer,
                "rating": rating,
            },
            timeout=30,
        )
    except requests.RequestException:
        return None, "后端服务暂时不可用，请确认 FastAPI 已启动。"

    if response.status_code == 201:
        return response.json(), None

    return None, get_error_detail(response)


def create_document_with_content_api(
    base_url: str,
    title: str,
    file_type: str,
    content: str,
) -> tuple[dict | None, str | None]:
    """Create and index a document through the FastAPI document endpoint."""
    try:
        response = requests.post(
            base_url + "/api/v1/db/documents/with-content",
            json={
                "title": title,
                "file_type": file_type,
                "content": content,
            },
            timeout=300,
        )
    except requests.RequestException:
        return None, "后端服务暂时不可用，请确认 FastAPI 已启动。"

    if response.status_code == 201:
        return response.json(), None

    return None, get_error_detail(response)


def upload_text_document_api(
    base_url: str,
    file_name: str,
    content: bytes,
    title: str,
) -> tuple[dict | None, str | None]:
    """Upload and index a txt document through the FastAPI upload endpoint."""
    data = {}

    if title != "":
        data["title"] = title

    try:
        response = requests.post(
            base_url + "/api/v1/db/documents/upload-text",
            data=data,
            files={
                "file": (
                    file_name,
                    content,
                    "text/plain",
                )
            },
            timeout=300,
        )
    except requests.RequestException:
        return None, "后端服务暂时不可用，请确认 FastAPI 已启动。"

    if response.status_code == 201:
        return response.json(), None

    return None, get_error_detail(response)


def get_error_detail(response) -> str:
    """Read a friendly error message from a FastAPI response."""
    try:
        data = response.json()
    except Exception:
        return "请求失败，请稍后再试。"

    message = get_unified_error_message(data)
    request_id = data.get("request_id")

    if isinstance(request_id, str) and request_id != "":
        return f"{message}（请求编号：{request_id}）"

    return message


def parse_sse_event_line(line: str) -> dict | None:
    if not line.startswith("data: "):
        return None

    data_text = line.removeprefix("data: ").strip()

    if data_text == "":
        return None

    return json.loads(data_text)


def get_unified_error_message(data: dict) -> str:
    error = data.get("error")

    if isinstance(error, dict):
        message = error.get("message")

        if isinstance(message, str) and message != "":
            return message

    detail = data.get("detail")

    if isinstance(detail, str):
        return detail

    if detail is not None:
        return str(detail)

    return "请求失败，请稍后再试。"
