"""Agent tools for the knowledge base."""

from typing import Callable
from backend.services.rag_retriever_service import retrieve_rag_snippets
from backend.config import DATABASE_PATH, DEFAULT_MIN_SCORE, DEFAULT_TOP_K
from backend.services.ollama_service import generate_with_ollama
from backend.services.prompt_service import build_rag_prompt
from backend.services.sqlite_document_repository import (
    create_chunks_table,
    create_connection,
    create_documents_table,
    find_document_from_db_by_id,
    list_chunks_by_document_id,
    list_documents_from_db_filtered,
)
from week03.keyword_extractor import extract_keyword

REFUSAL_ANSWER = "知识库中没有找到相关资料，暂时无法回答。"
MODEL_UNAVAILABLE_ANSWER = "本地模型暂时不可用，请稍后再试。"


def list_documents_tool(database_path: str = DATABASE_PATH) -> dict:
    """列出知识库中的文档。"""
    connection = create_connection(database_path)

    create_documents_table(connection)

    documents = list_documents_from_db_filtered(connection)

    connection.close()

    return {
        "documents": documents,
        "count": len(documents),
    }


def find_document_by_title_tool(
    title: str,
    database_path: str = DATABASE_PATH,
) -> dict:
    """根据文档标题查找文档，优先精确匹配，再尝试包含匹配。"""
    documents_result = list_documents_tool(database_path)

    for document in documents_result["documents"]:
        if document["title"] == title:
            return {
                "found": True,
                "document": document,
                "match_type": "exact",
            }

    for document in documents_result["documents"]:
        if title in document["title"]:
            return {
                "found": True,
                "document": document,
                "match_type": "contains",
            }

    return {
        "found": False,
        "document": None,
        "match_type": None,
    }


def read_document_chunks_tool(
    document_id: int,
    database_path: str = DATABASE_PATH,
) -> dict:
    """读取某一份文档的 chunks。"""
    connection = create_connection(database_path)

    create_documents_table(connection)
    create_chunks_table(connection)

    document = find_document_from_db_by_id(connection, document_id)

    if document is None:
        connection.close()

        return {
            "found": False,
            "document": None,
            "chunks": [],
        }

    chunks = list_chunks_by_document_id(connection, document_id)

    connection.close()

    return {
        "found": True,
        "document": document,
        "chunks": chunks,
    }


def search_knowledge_base_tool(
    question: str,
    database_path: str = DATABASE_PATH,
    top_k: int = DEFAULT_TOP_K,
    mode: str = "keyword",
    min_score: float = DEFAULT_MIN_SCORE,
    retriever_backend: str = "sqlite",
    postgresql_connection=None,
) -> dict:
    """根据用户问题搜索知识库片段。"""
    snippets = retrieve_rag_snippets(
        question=question,
        backend=retriever_backend,
        sqlite_database_path=database_path,
        postgresql_connection=postgresql_connection,
        top_k=top_k,
        mode=mode,
        min_score=min_score,
    )

    keyword = extract_keyword(question)

    return {
        "question": question,
        "keyword": keyword,
        "snippets": snippets,
        "count": len(snippets),
    }


def answer_with_context_tool(
    question: str,
    snippets: list[dict],
    generator: Callable[[str], str] = generate_with_ollama,
) -> dict:
    """根据检索到的上下文片段生成回答。"""
    if snippets == []:
        return refuse_answer_tool(question)

    prompt = build_rag_prompt(question, snippets)
    generation_error = ""

    try:
        answer = generator(prompt).strip()
    except Exception as error:
        answer = MODEL_UNAVAILABLE_ANSWER
        generation_error = str(error)

    citations = []

    for snippet in snippets:
        citations.append(
            {
                "title": snippet["title"],
                "text": snippet["text"],
                "path": snippet["path"],
            }
        )

    return {
        "question": question,
        "answer": answer,
        "generation_error": generation_error,
        "citations": citations,
    }


def refuse_answer_tool(question: str) -> dict:
    """在没有可靠依据时拒答。"""
    return {
        "question": question,
        "answer": REFUSAL_ANSWER,
        "citations": [],
    }


def ask_clarification_tool(
    question: str,
    missing_field: str,
) -> dict:
    """当用户问题缺少必要信息时，向用户追问。"""
    return {
        "question": question,
        "answer": f"请补充{missing_field}。",
        "citations": [],
    }
