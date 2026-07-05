from pydantic import BaseModel
from pydantic import BaseModel, Field


class Citation(BaseModel):
    title: str
    text: str
    path: str


class ChatResponse(BaseModel):
    question: str
    keyword: str
    answer: str
    citations: list[Citation] = Field(default_factory=list)