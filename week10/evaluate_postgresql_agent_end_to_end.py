import psycopg

from backend.config import DATABASE_URL, EMBEDDING_MODEL
from backend.services.database_url_service import is_postgresql_database
from backend.services.langgraph_agent import run_langgraph_agent
from backend.services.ollama_embedding_service import embed_with_ollama
from backend.services.ollama_service import generate_with_ollama
from backend.services.postgresql_document_indexing_service import (
    create_postgresql_document_with_chunks_and_embeddings,
)
from backend.services.postgresql_document_repository import (
    find_document_by_title_from_postgresql,
)
from week10.evaluate_postgresql_agent import is_postgresql_citation


END_TO_END_DOCUMENT_TITLE = "PostgreSQL Agent 端到端验收文档"
END_TO_END_DOCUMENT_CONTENT = (
    "员工参加外部培训需要提前提交申请。"
    "培训结束后需要提交学习总结。"
)
END_TO_END_QUESTION = "员工参加外部培训需要做什么？"


def ensure_end_to_end_document(
    connection,
    title: str = END_TO_END_DOCUMENT_TITLE,
    content: str = END_TO_END_DOCUMENT_CONTENT,
    embedder=embed_with_ollama,
    embedding_model: str = EMBEDDING_MODEL,
) -> dict:
    existing_document = find_document_by_title_from_postgresql(connection, title)

    if existing_document is not None:
        return {
            "created": False,
            "document": existing_document,
        }

    created = create_postgresql_document_with_chunks_and_embeddings(
        connection,
        title=title,
        file_type="md",
        content=content,
        embedder=embedder,
        embedding_model=embedding_model,
    )

    if created is None:
        return {
            "created": False,
            "document": None,
        }

    return {
        "created": True,
        "document": created["document"],
    }


def cites_expected_document(citations: list[dict], expected_title: str) -> bool:
    for citation in citations:
        if citation.get("title") == expected_title and is_postgresql_citation(citation):
            return True

    return False


def top_citation_matches_expected_document(
    citations: list[dict],
    expected_title: str,
) -> bool:
    if citations == []:
        return False

    top_citation = citations[0]

    return (
        top_citation.get("title") == expected_title
        and is_postgresql_citation(top_citation)
    )


def evaluate_end_to_end_agent_result(
    result: dict,
    expected_title: str,
) -> dict:
    citations = result.get("citations", [])
    has_valid_context = result.get("has_valid_context") is True
    cited_expected_document = cites_expected_document(citations, expected_title)
    top_citation_matched = top_citation_matches_expected_document(
        citations,
        expected_title,
    )
    passed = (
        has_valid_context
        and result.get("is_fallback") is False
        and top_citation_matched
    )

    return {
        "passed": passed,
        "answer": result.get("answer", ""),
        "has_valid_context": has_valid_context,
        "is_fallback": result.get("is_fallback", False),
        "citation_count": len(citations),
        "cited_expected_document": cited_expected_document,
        "top_citation_matched": top_citation_matched,
        "citations": citations,
    }


def evaluate_postgresql_agent_end_to_end(
    connection,
    title: str = END_TO_END_DOCUMENT_TITLE,
    content: str = END_TO_END_DOCUMENT_CONTENT,
    question: str = END_TO_END_QUESTION,
    top_k: int = 3,
    min_score: float = 0.6,
    mode: str = "precomputed_embedding",
    timeout_seconds: float = 30,
    embedder=embed_with_ollama,
    generator=generate_with_ollama,
) -> dict:
    document_result = ensure_end_to_end_document(
        connection,
        title=title,
        content=content,
        embedder=embedder,
    )

    if document_result["document"] is None:
        return {
            "passed": False,
            "document_created": False,
            "document": None,
            "question": question,
            "answer": "",
            "has_valid_context": False,
            "is_fallback": False,
            "citation_count": 0,
            "cited_expected_document": False,
            "top_citation_matched": False,
            "citations": [],
        }

    agent_result = run_langgraph_agent(
        question=question,
        top_k=top_k,
        mode=mode,
        min_score=min_score,
        timeout_seconds=timeout_seconds,
        retriever_backend="postgresql",
        postgresql_connection=connection,
        generator=generator,
    )

    evaluation = evaluate_end_to_end_agent_result(
        agent_result,
        expected_title=title,
    )

    return {
        "passed": evaluation["passed"],
        "document_created": document_result["created"],
        "document": document_result["document"],
        "question": question,
        "top_k": top_k,
        "min_score": min_score,
        "mode": mode,
        "retriever_backend": "postgresql",
        **evaluation,
    }


def main():
    if not is_postgresql_database(DATABASE_URL):
        print("DATABASE_URL 不是 PostgreSQL 地址，已停止。")
        print("当前 DATABASE_URL:", DATABASE_URL)
        return

    with psycopg.connect(DATABASE_URL) as connection:
        result = evaluate_postgresql_agent_end_to_end(connection)

    print("PostgreSQL Agent 端到端业务验收完成。")
    print("是否通过：", result["passed"])
    print("是否新建文档：", result["document_created"])
    print("文档标题：", result["document"]["title"] if result["document"] else "")
    print("问题：", result["question"])
    print("检索后端：", result["retriever_backend"])
    print("检索模式：", result["mode"])
    print("top_k：", result["top_k"])
    print("min_score：", result["min_score"])
    print("has_valid_context：", result["has_valid_context"])
    print("是否兜底回答：", result["is_fallback"])
    print("是否引用验收文档：", result["cited_expected_document"])
    print("Top1 是否引用验收文档：", result["top_citation_matched"])
    print("引用数量：", result["citation_count"])
    print("回答：", result["answer"])

    for index, citation in enumerate(result["citations"], start=1):
        print(f"[{index}] {citation['title']} - {citation['path']}")


if __name__ == "__main__":
    main()
