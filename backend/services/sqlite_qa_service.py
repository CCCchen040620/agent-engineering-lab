from backend.services.sqlite_document_repository import (
    create_connection,
    create_chunks_table,
    create_documents_table,
    search_chunks_with_document_by_text,
)
from week03.answer_with_citation import build_answer
from week03.keyword_extractor import extract_keyword
from week04.settings import SQLITE_DATABASE_PATH
from week05.models import ChatResponse, Citation


def build_sqlite_chat_response(question: str, database_path: str = SQLITE_DATABASE_PATH) -> ChatResponse:
    keyword = extract_keyword(question)

    connection = create_connection(database_path)

    create_documents_table(connection)
    create_chunks_table(connection)

    chunk_results = search_chunks_with_document_by_text(connection, keyword)

    connection.close()

    snippets = []

    for chunk in chunk_results:
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