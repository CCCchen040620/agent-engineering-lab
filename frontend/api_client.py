"""Small HTTP helpers used by Streamlit pages."""

import requests


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
    """Read FastAPI error detail from a response."""
    try:
        detail = response.json()["detail"]
    except Exception:
        return "请求失败，请稍后再试。"

    if isinstance(detail, str):
        return detail

    return str(detail)
