from typing import Callable

from fastapi import APIRouter, Depends, Query

from backend.config import DEFAULT_MIN_SCORE, DEFAULT_TOP_K
from backend.routers.db_documents import get_database_path
from backend.services.langgraph_agent import run_langgraph_agent
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
):
    return run_langgraph_agent(
        question=request.question,
        database_path=database_path,
        top_k=top_k,
        mode=mode,
        min_score=min_score,
        generator=generator,
    )