import argparse

import psycopg

from backend.config import DATABASE_URL
from backend.services.database_url_service import is_postgresql_database
from backend.services.langgraph_agent import run_langgraph_agent
from backend.services.ollama_service import generate_with_ollama
from backend.services.postgresql_document_repository import (
    find_document_by_title_from_postgresql,
)
from week10.evaluate_postgresql_agent import is_postgresql_citation


REFUSAL_MARKERS = [
    "知识库中没有找到相关资料",
    "暂时无法回答",
]


def answer_is_refusal(answer: str) -> bool:
    for marker in REFUSAL_MARKERS:
        if marker in answer:
            return True

    return False


def citation_matches_document(citation: dict, title: str) -> bool:
    return citation.get("title") == title and is_postgresql_citation(citation)


def citations_include_document(citations: list[dict], title: str) -> bool:
    for citation in citations:
        if citation_matches_document(citation, title):
            return True

    return False


def top_citation_matches_document(citations: list[dict], title: str) -> bool:
    if citations == []:
        return False

    return citation_matches_document(citations[0], title)


def get_agent_flow_failure_reason(result: dict, title: str) -> str:
    citations = result.get("citations", [])
    answer = result.get("answer", "")

    if result.get("has_valid_context") is not True:
        return "invalid_context"

    if result.get("is_fallback") is True:
        return "fallback_answer"

    if answer_is_refusal(answer):
        return "refusal_answer"

    if not citations_include_document(citations, title):
        return "expected_document_not_cited"

    if not top_citation_matches_document(citations, title):
        return "top_citation_mismatch"

    return ""


def evaluate_agent_result_for_document(result: dict, title: str) -> dict:
    citations = result.get("citations", [])
    failure_reason = get_agent_flow_failure_reason(result, title)

    return {
        "passed": failure_reason == "",
        "failure_reason": failure_reason,
        "answer": result.get("answer", ""),
        "has_valid_context": result.get("has_valid_context") is True,
        "is_fallback": result.get("is_fallback", False),
        "citation_count": len(citations),
        "cited_expected_document": citations_include_document(citations, title),
        "top_citation_matched": top_citation_matches_document(citations, title),
        "citations": citations,
        "snippets": result.get("snippets", []),
    }


def evaluate_document_ingestion_agent_flow(
    connection,
    title: str,
    question: str,
    top_k: int = 3,
    min_score: float = 0.6,
    mode: str = "precomputed_embedding",
    timeout_seconds: float = 30,
    generator=generate_with_ollama,
    agent_runner=run_langgraph_agent,
) -> dict:
    document = find_document_by_title_from_postgresql(connection, title)

    if document is None:
        return {
            "passed": False,
            "failure_reason": "document_not_found",
            "title": title,
            "question": question,
            "document": None,
            "top_k": top_k,
            "min_score": min_score,
            "mode": mode,
            "retriever_backend": "postgresql",
            "answer": "",
            "has_valid_context": False,
            "is_fallback": False,
            "citation_count": 0,
            "cited_expected_document": False,
            "top_citation_matched": False,
            "citations": [],
            "snippets": [],
        }

    agent_result = agent_runner(
        question=question,
        top_k=top_k,
        mode=mode,
        min_score=min_score,
        timeout_seconds=timeout_seconds,
        retriever_backend="postgresql",
        postgresql_connection=connection,
        generator=generator,
    )
    evaluation = evaluate_agent_result_for_document(agent_result, title)

    return {
        "title": title,
        "question": question,
        "document": document,
        "top_k": top_k,
        "min_score": min_score,
        "mode": mode,
        "retriever_backend": "postgresql",
        **evaluation,
    }


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate whether an ingested PostgreSQL document can answer through the Agent.",
    )
    parser.add_argument("--title", required=True)
    parser.add_argument("--question", required=True)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--min-score", type=float, default=0.6)
    parser.add_argument("--timeout-seconds", type=float, default=30)
    return parser


def print_evaluation_result(result: dict) -> None:
    print("PostgreSQL 文档入库 Agent 验收完成。")
    print("是否通过：", result["passed"])
    print("失败原因：", result["failure_reason"])
    print("文档标题：", result["title"])
    print("问题：", result["question"])
    print("检索后端：", result["retriever_backend"])
    print("检索模式：", result["mode"])
    print("top_k：", result["top_k"])
    print("min_score：", result["min_score"])
    print("has_valid_context：", result["has_valid_context"])
    print("是否兜底回答：", result["is_fallback"])
    print("是否引用目标文档：", result["cited_expected_document"])
    print("Top1 是否引用目标文档：", result["top_citation_matched"])
    print("引用数量：", result["citation_count"])
    print("回答：", result["answer"])

    for index, citation in enumerate(result["citations"], start=1):
        print(f"[{index}] {citation['title']} - {citation['path']}")


def main():
    if not is_postgresql_database(DATABASE_URL):
        print("DATABASE_URL 不是 PostgreSQL 地址，已停止。")
        print("当前 DATABASE_URL:", DATABASE_URL)
        return

    parser = build_argument_parser()
    args = parser.parse_args()

    with psycopg.connect(DATABASE_URL) as connection:
        result = evaluate_document_ingestion_agent_flow(
            connection,
            title=args.title,
            question=args.question,
            top_k=args.top_k,
            min_score=args.min_score,
            timeout_seconds=args.timeout_seconds,
        )

    print_evaluation_result(result)


if __name__ == "__main__":
    main()
