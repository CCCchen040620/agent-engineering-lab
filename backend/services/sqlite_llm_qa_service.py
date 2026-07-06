from typing import Callable

from backend.services.ollama_service import generate_with_ollama
from backend.services.prompt_service import build_rag_prompt
from backend.services.ranking_service import rank_chunks
from backend.services.sqlite_document_repository import (
    create_chunks_table,
    create_connection,
    create_documents_table,
    search_chunks_with_document_by_text,
)
from backend.services.sqlite_vector_search_service import search_sqlite_chunks_by_similarity
from week03.keyword_extractor import extract_keyword
from week04.settings import SQLITE_DATABASE_PATH
from week05.models import ChatResponse, Citation


def search_sqlite_snippets(
    question: str,
    database_path: str,
    top_k: int = 3,
    mode: str = "vector",
    min_score: float = 0.3,
) -> tuple[str, list[dict]]:
    keyword = extract_keyword(question)

    if mode == "vector":
        snippets = search_sqlite_chunks_by_similarity(
            database_path=database_path,
            query=question,
            top_k=top_k,
            min_score=min_score,
        )

        return keyword, snippets

    connection = create_connection(database_path)

    create_documents_table(connection)
    create_chunks_table(connection)

    chunk_results = search_chunks_with_document_by_text(connection, keyword)
    chunk_results = rank_chunks(chunk_results, keyword)

    connection.close()

    snippets = []

    for chunk in chunk_results[:top_k]:
        snippets.append(
            {
                "title": chunk["document_title"],
                "path": "sqlite://" + str(chunk["document_id"]),
                "text": chunk["text"],
            }
        )

    return keyword, snippets


def build_sqlite_llm_chat_response(
    question: str,
    database_path: str = SQLITE_DATABASE_PATH,
    top_k: int = 3,
    mode: str = "vector",
    min_score: float = 0.3,
    generator: Callable[[str], str] = generate_with_ollama,
) -> ChatResponse:
    keyword, snippets = search_sqlite_snippets(
        question=question,
        database_path=database_path,
        top_k=top_k,
        mode=mode,
        min_score=min_score,
    )

    citations = []

    for snippet in snippets:
        citations.append(
            Citation(
                title=snippet["title"],
                text=snippet["text"],
                path=snippet["path"],
            )
        )

    if snippets == []:
        answer = "知识库中没有找到相关资料，暂时无法回答。"
    else:
        prompt = build_rag_prompt(question, snippets)

        try:
            answer = generator(prompt).strip()
        except Exception:
            answer = "本地模型暂时不可用，请稍后再试。"

    return ChatResponse(
        question=question,
        keyword=keyword,
        answer=answer,
        citations=citations,
    )