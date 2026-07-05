from pydantic import BaseModel


class Citation(BaseModel):
    title: str
    text: str
    path: str


class ChatResponse(BaseModel):
    question: str
    keyword: str
    answer: str
    citations: list[Citation]