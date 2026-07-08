from fastapi import APIRouter, Query

from backend.services.langgraph_memory_service import chat_with_memory
from week05.models import ChatRequest


router = APIRouter(prefix="/api/v1/memory-demo")


@router.post("/chat")
def memory_demo_chat(
    request: ChatRequest,
    thread_id: str = Query(min_length=1),
):
    return chat_with_memory(
        message=request.question,
        thread_id=thread_id,
    )