from pydantic import BaseModel
from pydantic import BaseModel, Field
from typing import Literal


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


class FeedbackCreateRequest(BaseModel):
    question: str = Field(min_length=1)
    answer: str = Field(min_length=1)
    rating: Literal["helpful", "not_helpful"]


class Feedback(BaseModel):
    id: int
    question: str = Field(min_length=1)
    answer: str = Field(min_length=1)
    rating: Literal["helpful", "not_helpful"]


class DocumentCreateWithContentRequest(BaseModel):
    title: str = Field(min_length=1)
    file_type: str = Field(min_length=1)
    content: str = Field(min_length=1)


class Chunk(BaseModel):
    id: int
    document_id: int
    text: str = Field(min_length=1)


class ConversationCreateRequest(BaseModel):
    title: str = Field(min_length=1)


class MessageCreateRequest(BaseModel):
    role: str = Field(min_length=1)
    content: str = Field(min_length=1)


class VectorSearchRequest(BaseModel):
    embedding: list[float]
    top_k: int = 3


class VectorSearchResult(BaseModel):
    chunk_id: int
    document_id: int
    document_title: str = Field(min_length=1)
    text: str = Field(min_length=1)
    distance: float
    score: float