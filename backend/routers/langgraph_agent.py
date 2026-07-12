import json
import psycopg

from typing import Callable

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from backend.services.sqlite_document_repository import create_connection
from backend.services.sqlite_conversation_repository import (
    add_message,
    create_conversations_table,
    create_messages_table,
    find_conversation_by_id,
    list_messages_by_conversation,
    update_conversation_summary,
)
from backend.config import (
    DATABASE_URL,
    DEFAULT_MIN_SCORE,
    DEFAULT_TOP_K,
    LANGGRAPH_AGENT_TIMEOUT_SECONDS,
    RAG_RETRIEVER_BACKEND,
)
from backend.routers.db_documents import get_database_path
from backend.routers.rate_limit import enforce_heavy_request_rate_limit
from backend.services.langgraph_agent import run_langgraph_agent
from backend.services.conversation_summary_service import (
    build_conversation_summary,
)
from backend.services.ollama_service import generate_with_ollama
from backend.services.database_url_service import is_postgresql_database
from week05.models import ChatRequest


router = APIRouter(prefix="/api/v1/langgraph-agent")


def get_langgraph_agent_generator() -> Callable[[str], str]:
    return generate_with_ollama


def get_langgraph_postgresql_database_url() -> str:
    return DATABASE_URL


def ensure_supported_retriever_backend(retriever_backend: str):
    if retriever_backend not in ["sqlite", "postgresql"]:
        raise HTTPException(
            status_code=400,
            detail="Unsupported retriever_backend.",
        )


def create_postgresql_connection_for_retriever(
    retriever_backend: str,
    database_url: str,
):
    ensure_supported_retriever_backend(retriever_backend)

    if retriever_backend != "postgresql":
        return None

    if not is_postgresql_database(database_url):
        raise HTTPException(
            status_code=400,
            detail="DATABASE_URL must be a PostgreSQL URL to use PostgreSQL retriever.",
        )

    return psycopg.connect(database_url)

def split_text_for_stream(text: str, chunk_size: int = 20) -> list[str]:
    chunks = []

    for start_index in range(0, len(text), chunk_size):
        chunks.append(text[start_index:start_index + chunk_size])

    return chunks


def format_stream_event(event: dict) -> str:
    return "data: " + json.dumps(event, ensure_ascii=False) + "\n\n"


def stream_langgraph_agent_result(result: dict):
    answer = result["answer"]

    for chunk in split_text_for_stream(answer):
        yield format_stream_event(
            {
                "type": "delta",
                "content": chunk,
            }
        )

    yield format_stream_event(
        {
            "type": "metadata",
            "keyword": result["keyword"],
            "citation_count": len(result["citations"]),
            "is_fallback": result.get("is_fallback", False),
            "is_timeout": result.get("is_timeout", False),
        }
    )

    yield format_stream_event(
        {
            "type": "done",
        }
    )


@router.post("/chat")
def langgraph_agent_chat(
    request: ChatRequest,
    top_k: int = Query(default=DEFAULT_TOP_K, ge=1, le=5),
    mode: str = "keyword",
    min_score: float = Query(default=DEFAULT_MIN_SCORE, ge=0, le=1),
    timeout_seconds: float = Query(
        default=LANGGRAPH_AGENT_TIMEOUT_SECONDS,
        ge=1,
        le=120,
    ),
    retriever_backend: str = Query(default=RAG_RETRIEVER_BACKEND),
    database_path: str = Depends(get_database_path),
    postgresql_database_url: str = Depends(get_langgraph_postgresql_database_url),
    generator: Callable[[str], str] = Depends(get_langgraph_agent_generator),
    _rate_limit: None = Depends(enforce_heavy_request_rate_limit),
):
    postgresql_connection = create_postgresql_connection_for_retriever(
        retriever_backend=retriever_backend,
        database_url=postgresql_database_url,
    )

    try:
        return run_langgraph_agent(
            question=request.question,
            database_path=database_path,
            top_k=top_k,
            mode=mode,
            min_score=min_score,
            timeout_seconds=timeout_seconds,
            retriever_backend=retriever_backend,
            postgresql_connection=postgresql_connection,
            generator=generator,
        )
    finally:
        if postgresql_connection is not None:
            postgresql_connection.close()


@router.post("/chat/stream")
def langgraph_agent_chat_stream(
    request: ChatRequest,
    top_k: int = Query(default=DEFAULT_TOP_K, ge=1, le=5),
    mode: str = "keyword",
    min_score: float = Query(default=DEFAULT_MIN_SCORE, ge=0, le=1),
    timeout_seconds: float = Query(
        default=LANGGRAPH_AGENT_TIMEOUT_SECONDS,
        ge=1,
        le=120,
    ),
    retriever_backend: str = Query(default=RAG_RETRIEVER_BACKEND),
    database_path: str = Depends(get_database_path),
    generator: Callable[[str], str] = Depends(get_langgraph_agent_generator),
    _rate_limit: None = Depends(enforce_heavy_request_rate_limit),
):
    ensure_postgresql_retriever_not_enabled_for_endpoint(retriever_backend)

    result = run_langgraph_agent(
        question=request.question,
        database_path=database_path,
        top_k=top_k,
        mode=mode,
        min_score=min_score,
        timeout_seconds=timeout_seconds,
        retriever_backend=retriever_backend,
        generator=generator,
    )

    return StreamingResponse(
        stream_langgraph_agent_result(result),
        media_type="text/event-stream",
    )

    
@router.post("/conversations/{conversation_id}/chat")
def langgraph_agent_conversation_chat(
    conversation_id: int,
    request: ChatRequest,
    top_k: int = Query(default=DEFAULT_TOP_K, ge=1, le=5),
    mode: str = "keyword",
    min_score: float = Query(default=DEFAULT_MIN_SCORE, ge=0, le=1),
    timeout_seconds: float = Query(
        default=LANGGRAPH_AGENT_TIMEOUT_SECONDS,
        ge=1,
        le=120,
    ),
    retriever_backend: str = Query(default=RAG_RETRIEVER_BACKEND),
    database_path: str = Depends(get_database_path),
    generator: Callable[[str], str] = Depends(get_langgraph_agent_generator),
    _rate_limit: None = Depends(enforce_heavy_request_rate_limit),
):
    connection = create_connection(database_path)

    create_conversations_table(connection)
    create_messages_table(connection)

    conversation = find_conversation_by_id(connection, conversation_id)

    if conversation is None:
        connection.close()

        raise HTTPException(
            status_code=404,
            detail="会话不存在。",
        )

    messages = list_messages_by_conversation(
        connection,
        conversation_id=conversation_id,
    )
    ensure_postgresql_retriever_not_enabled_for_endpoint(retriever_backend)

    result = run_langgraph_agent(
        question=request.question,
        database_path=database_path,
        top_k=top_k,
        mode=mode,
        min_score=min_score,
        timeout_seconds=timeout_seconds,
        retriever_backend=retriever_backend,
        generator=generator,
        messages=messages,
        conversation_summary=conversation["summary"],
    )

    user_metadata = {
        "question": request.question,
    }

    user_message = add_message(
        connection,
        conversation_id=conversation_id,
        role="user",
        content=request.question,
        metadata=user_metadata,
    )

    assistant_metadata = {
        "intent": result["intent"],
        "keyword": result["keyword"],
        "citations": result["citations"],
        "steps": result["steps"],
    }

    assistant_message = add_message(
        connection,
        conversation_id=conversation_id,
        role="assistant",
        content=result["answer"],
        metadata=assistant_metadata,
    )

    updated_messages = list_messages_by_conversation(
        connection,
        conversation_id=conversation_id,
    )

    conversation_summary = build_conversation_summary(updated_messages)

    updated_conversation = update_conversation_summary(
        connection,
        conversation_id=conversation_id,
        summary=conversation_summary,
    )

    connection.close()

    result["conversation_id"] = conversation_id
    result["conversation_summary"] = updated_conversation["summary"]
    result["saved_messages"] = [
        user_message,
        assistant_message,
    ]

    return result


def ensure_postgresql_retriever_not_enabled_for_endpoint(
    retriever_backend: str,
):
    if retriever_backend == "postgresql":
        raise HTTPException(
            status_code=400,
            detail="PostgreSQL retriever is not enabled for this endpoint yet.",
        )