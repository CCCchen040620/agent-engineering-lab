from fastapi import APIRouter, Depends, Query

from typing import Callable
from backend.services.ollama_service import generate_with_ollama
from backend.config import DEFAULT_MIN_SCORE, DEFAULT_TOP_K
from backend.routers.db_documents import get_database_path
from backend.services.simple_agent import run_simple_agent
from week05.models import ChatRequest


router = APIRouter(prefix="/api/v1/agent")

def get_agent_generator() -> Callable[[str], str]:
    return generate_with_ollama

@router.post("/chat")
def agent_chat(
    request: ChatRequest,
    top_k: int = Query(default=DEFAULT_TOP_K, ge=1, le=5),
    mode: str = "keyword",
    min_score: float = Query(default=DEFAULT_MIN_SCORE, ge=0, le=1),
    database_path: str = Depends(get_database_path),
    generator: Callable[[str], str] = Depends(get_agent_generator),
):
    return run_simple_agent(
        question=request.question,
        database_path=database_path,
        top_k=top_k,
        mode=mode,
        min_score=min_score,
        generator=generator,
    )