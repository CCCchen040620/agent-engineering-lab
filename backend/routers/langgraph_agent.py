from typing import Callable

from fastapi import APIRouter, Depends, HTTPException, Query
from backend.services.sqlite_document_repository import create_connection
from backend.services.sqlite_conversation_repository import (
    add_message,
    create_conversations_table,
    create_messages_table,
    find_conversation_by_id,
    list_messages_by_conversation,
    update_conversation_summary,
)
from backend.config import DEFAULT_MIN_SCORE, DEFAULT_TOP_K
from backend.routers.db_documents import get_database_path
from backend.routers.rate_limit import enforce_heavy_request_rate_limit
from backend.services.langgraph_agent import run_langgraph_agent
from backend.services.conversation_summary_service import (
    build_conversation_summary,
)
from backend.services.ollama_service import generate_with_ollama
from week05.models import ChatRequest


router = APIRouter(prefix="/api/v1/langgraph-agent")


def get_langgraph_agent_generator() -> Callable[[str], str]:
    return generate_with_ollama


@router.post("/chat")
def langgraph_agent_chat(
    request: ChatRequest,
    top_k: int = Query(default=DEFAULT_TOP_K, ge=1, le=5),
    mode: str = "keyword",
    min_score: float = Query(default=DEFAULT_MIN_SCORE, ge=0, le=1),
    database_path: str = Depends(get_database_path),
    generator: Callable[[str], str] = Depends(get_langgraph_agent_generator),
    _rate_limit: None = Depends(enforce_heavy_request_rate_limit),
):
    return run_langgraph_agent(
        question=request.question,
        database_path=database_path,
        top_k=top_k,
        mode=mode,
        min_score=min_score,
        generator=generator,
    )


@router.post("/conversations/{conversation_id}/chat")
def langgraph_agent_conversation_chat(
    conversation_id: int,
    request: ChatRequest,
    top_k: int = Query(default=DEFAULT_TOP_K, ge=1, le=5),
    mode: str = "keyword",
    min_score: float = Query(default=DEFAULT_MIN_SCORE, ge=0, le=1),
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

    result = run_langgraph_agent(
        question=request.question,
        database_path=database_path,
        top_k=top_k,
        mode=mode,
        min_score=min_score,
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
