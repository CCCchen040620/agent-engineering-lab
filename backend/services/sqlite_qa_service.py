from backend.services.sqlite_document_repository import (
    create_connection,
    create_chunks_table,
    create_documents_table,
    search_chunks_with_document_by_text,
)
from backend.services.sqlite_vector_search_service import search_sqlite_chunks_by_similarity
from week03.answer_with_citation import build_answer
from week03.keyword_extractor import extract_keyword
from week05.models import ChatResponse, Citation
from backend.services.ranking_service import rank_chunks
from backend.config import DATABASE_PATH


def build_sqlite_chat_response(
    question: str,
    database_path: str = DATABASE_PATH,
    top_k: int = 3,
    mode: str = "keyword",
) -> ChatResponse:
    keyword = extract_keyword(question)

    if mode == "vector":
        snippets = search_sqlite_chunks_by_similarity(
            database_path=database_path,
            query=question,
            top_k=top_k,
        )
    else:
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

    answer = build_answer(question, snippets, keyword)

    citations = []

    for snippet in snippets[:3]:
        citations.append(
            Citation(
                title=snippet["title"],
                text=snippet["text"],
                path=snippet["path"],
            )
        )

    return ChatResponse(
        question=question,
        keyword=keyword,
        answer=answer,
        citations=citations,
    )