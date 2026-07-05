from pydantic import BaseModel
from pydantic import BaseModel, Field


class Citation(BaseModel):
    title: str
    text: str = Field(min_length=1)
    path: str


class ChatResponse(BaseModel):
    question: str
    keyword: str
    answer: str
    citations: list[Citation] = Field(default_factory=list)