from pydantic import BaseModel
from pydantic import BaseModel, Field


class Citation(BaseModel):
    title: str = Field(min_length=1)
    text: str = Field(min_length=1)
    path: str = Field(min_length=1)


class ChatResponse(BaseModel):
    question: str
    keyword: str
    answer: str
    citations: list[Citation] = Field(default_factory=list)