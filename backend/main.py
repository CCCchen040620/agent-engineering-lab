from fastapi import FastAPI

from week04.structured_answer import build_structured_answer
from week05.models import ChatRequest, ChatResponse


app = FastAPI(title="Enterprise Knowledge Base Agent")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/api/v1/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    return build_structured_answer(request.question)