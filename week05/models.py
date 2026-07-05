from pydantic import BaseModel
from pydantic import BaseModel, Field


class Citation(BaseModel):
    title: str = Field(min_length=1)
    text: str = Field(min_length=1)
    path: str = Field(min_length=1)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1)


class ChatResponse(BaseModel):
    question: str = Field(min_length=1)
    keyword: str = Field(min_length=1)
    answer: str = Field(min_length=1)
    citations: list[Citation] = Field(default_factory=list)


class Document(BaseModel):
    id: int
    title: str = Field(min_length=1)
    file_type: str = Field(min_length=1)
    chunk_count: int
    is_indexed: bool


class DocumentCreateRequest(BaseModel):
    title: str = Field(min_length=1)
    file_type: str = Field(min_length=1)
    chunk_count: int
    is_indexed: bool = False