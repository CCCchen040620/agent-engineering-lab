"""Small HTTP helpers used by Streamlit pages."""

import json

import requests


def get_info_api(base_url: str) -> tuple[dict | None, str | None]:
    """Get backend feature and capability information."""
    try:
        response = requests.get(
            base_url + "/api/v1/info",
            timeout=30,
        )
    except requests.RequestException:
        return None, "后端服务暂时不可用，请确认 FastAPI 已启动。"

    if response.status_code == 200:
        return response.json(), None

    return None, get_error_detail(response)


def find_rag_backend_capabilities(
    info: dict | None,
    backend: str,
) -> dict | None:
    if info is None:
        return None

    normalized_backend = backend.strip().lower()

    for capabilities in info.get("rag_backends", []):
        if capabilities.get("backend") == normalized_backend:
            return capabilities

    return None


def rag_backend_supports_feature(
    info: dict | None,
    backend: str,
    feature: str,
) -> bool:
    capabilities = find_rag_backend_capabilities(info, backend)

    if capabilities is None:
        return True

    return feature in capabilities.get("supported_features", [])


def get_document_api_prefix(backend: str) -> str:
    normalized_backend = backend.strip().lower()

    if normalized_backend == "postgresql":
        return "/api/v1/postgresql"

    return "/api/v1/db"


def list_documents_api(
    base_url: str,
    backend: str = "sqlite",
    source: str | None = None,
) -> tuple[list[dict] | None, str | None]:
    """List documents from the selected backend."""
    endpoint = base_url + get_document_api_prefix(backend) + "/documents"
    params = {}

    if backend.strip().lower() == "postgresql" and source not in (None, ""):
        params["source"] = source

    try:
        if params == {}:
            response = requests.get(endpoint, timeout=30)
        else:
            response = requests.get(endpoint, params=params, timeout=30)
    except requests.RequestException:
        return None, "后端服务暂时不可用，请确认 FastAPI 已启动。"

    if response.status_code == 200:
        return response.json(), None

    return None, get_error_detail(response)


def list_document_chunks_api(
    base_url: str,
    document_id: int,
    backend: str = "sqlite",
) -> tuple[list[dict] | None, str | None]:
    """List document chunks from the selected backend."""
    try:
        response = requests.get(
            base_url
            + get_document_api_prefix(backend)
            + f"/documents/{document_id}/chunks",
            timeout=30,
        )
    except requests.RequestException:
        return None, "后端服务暂时不可用，请确认 FastAPI 已启动。"

    if response.status_code == 200:
        return response.json(), None

    return None, get_error_detail(response)


def list_postgresql_document_embedding_status_api(
    base_url: str,
) -> tuple[list[dict] | None, str | None]:
    """List PostgreSQL document embedding status from the backend."""
    try:
        response = requests.get(
            base_url + "/api/v1/postgresql/documents/embedding-status",
            timeout=30,
        )
    except requests.RequestException:
        return None, "后端服务暂时不可用，请确认 FastAPI 已启动。"

    if response.status_code == 200:
        return response.json(), None

    return None, get_error_detail(response)


def list_postgresql_document_source_summary_api(
    base_url: str,
) -> tuple[list[dict] | None, str | None]:
    """List PostgreSQL document counts grouped by source."""
    try:
        response = requests.get(
            base_url + "/api/v1/postgresql/documents/source-summary",
            timeout=30,
        )
    except requests.RequestException:
        return None, "后端服务暂时不可用，请确认 FastAPI 已启动。"

    if response.status_code == 200:
        return response.json(), None

    return None, get_error_detail(response)


def backfill_postgresql_embeddings_api(
    base_url: str,
) -> tuple[dict | None, str | None]:
    """Backfill missing PostgreSQL chunk embeddings through the backend."""
    try:
        response = requests.post(
            base_url + "/api/v1/postgresql/embeddings/backfill",
            timeout=300,
        )
    except requests.RequestException:
        return None, "后端服务暂时不可用，请确认 FastAPI 已启动。"

    if response.status_code == 200:
        return response.json(), None

    return None, get_error_detail(response)


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
    retriever_backend: str = "sqlite",
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
                "retriever_backend": retriever_backend,
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
    retriever_backend: str = "sqlite",
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
                "retriever_backend": retriever_backend,
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


def create_postgresql_document_with_content_api(
    base_url: str,
    title: str,
    file_type: str,
    content: str,
) -> tuple[dict | None, str | None]:
    """Create and index a document through the PostgreSQL document endpoint."""
    try:
        response = requests.post(
            base_url + "/api/v1/postgresql/documents/with-content",
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


def delete_postgresql_document_api(
    base_url: str,
    document_id: int,
) -> tuple[dict | None, str | None]:
    """Delete a PostgreSQL document by id through the backend."""
    try:
        response = requests.delete(
            base_url + f"/api/v1/postgresql/documents/{document_id}",
            timeout=30,
        )
    except requests.RequestException:
        return None, "后端服务暂时不可用，请确认 FastAPI 已启动。"

    if response.status_code == 200:
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


def list_tasks_api(
    base_url: str,
    status: str | None = None,
    order: str | None = None,
) -> list[dict]:
    params = {}

    if status not in (None, "", "全部"):
        params["status"] = status

    if order in ("asc", "desc"):
        params["order"] = order

    response = requests.get(
        base_url + "/api/v1/tasks",
        params=params,
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def get_task_api(base_url: str, task_id: int) -> dict:
    response = requests.get(
        base_url + f"/api/v1/tasks/{task_id}",
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def create_task_api(
    base_url: str,
    task_type: str,
    payload: dict | None = None,
) -> dict:
    response = requests.post(
        base_url + "/api/v1/tasks",
        json={
            "type": task_type,
            "payload": payload or {},
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def run_task_async_api(base_url: str, task_id: int) -> dict:
    response = requests.post(
        base_url + f"/api/v1/tasks/{task_id}/run-async",
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def run_postgresql_embedding_backfill_task_api(base_url: str) -> dict:
    response = requests.post(
        base_url + "/api/v1/tasks/postgresql-embedding-backfill",
        timeout=60,
    )
    response.raise_for_status()
    return response.json()
