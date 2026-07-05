from fastapi import APIRouter

from week04.structured_answer import build_structured_answer
from week05.models import ChatRequest, ChatResponse


router = APIRouter(prefix="/api/v1")


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    return build_structured_answer(request.question)