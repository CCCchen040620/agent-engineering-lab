import argparse

import psycopg

from backend.config import DATABASE_URL
from backend.services.database_url_service import is_postgresql_database
from backend.services.postgresql_document_repository import (
    find_document_by_title_from_postgresql,
    list_chunks_by_document_from_postgresql,
)
from backend.services.postgresql_embedding_repository import (
    summarize_document_embedding_status_from_postgresql,
)
from backend.services.postgresql_natural_language_search_service import (
    search_postgresql_chunks_by_question,
)


def find_embedding_status_by_document_title(
    connection,
    title: str,
) -> dict | None:
    statuses = summarize_document_embedding_status_from_postgresql(connection)

    for status in statuses:
        if status["title"] == title:
            return status

    return None


def top_result_matches_document(results: list[dict], title: str) -> bool:
    if results == []:
        return False

    return results[0].get("document_title") == title


def search_results_include_document(results: list[dict], title: str) -> bool:
    for result in results:
        if result.get("document_title") == title:
            return True

    return False


def validate_postgresql_document_ingestion(
    connection,
    title: str,
    question: str,
    top_k: int = 3,
    min_score: float = 0.6,
    searcher=search_postgresql_chunks_by_question,
) -> dict:
    document = find_document_by_title_from_postgresql(connection, title)

    if document is None:
        return {
            "passed": False,
            "failure_reason": "document_not_found",
            "title": title,
            "question": question,
            "document_found": False,
            "document": None,
            "chunk_count": 0,
            "embedding_count": 0,
            "is_embedding_complete": False,
            "retrieval_count": 0,
            "retrieved_expected_document": False,
            "top1_matches_document": False,
            "top1_result": None,
            "results": [],
            "top_k": top_k,
            "min_score": min_score,
        }

    chunks = list_chunks_by_document_from_postgresql(
        connection,
        document_id=document["id"],
    )
    embedding_status = find_embedding_status_by_document_title(
        connection,
        title,
    )

    if embedding_status is None:
        embedding_status = {
            "embedding_count": 0,
            "is_embedding_complete": False,
        }

    search_result = searcher(
        connection,
        question=question,
        top_k=top_k,
        min_score=min_score,
    )
    results = search_result.get("results", [])
    top1_result = results[0] if results else None

    chunk_count = len(chunks)
    embedding_count = embedding_status["embedding_count"]
    is_embedding_complete = embedding_status["is_embedding_complete"]
    retrieved_expected_document = search_results_include_document(results, title)
    top1_matched = top_result_matches_document(results, title)

    if chunk_count == 0:
        failure_reason = "no_chunks"
    elif not is_embedding_complete:
        failure_reason = "embedding_incomplete"
    elif not retrieved_expected_document:
        failure_reason = "document_not_retrieved"
    elif not top1_matched:
        failure_reason = "top1_document_mismatch"
    else:
        failure_reason = ""

    passed = failure_reason == ""

    return {
        "passed": passed,
        "failure_reason": failure_reason,
        "title": title,
        "question": question,
        "document_found": True,
        "document": document,
        "chunk_count": chunk_count,
        "embedding_count": embedding_count,
        "is_embedding_complete": is_embedding_complete,
        "retrieval_count": len(results),
        "retrieved_expected_document": retrieved_expected_document,
        "top1_matches_document": top1_matched,
        "top1_result": top1_result,
        "results": results,
        "top_k": top_k,
        "min_score": min_score,
    }


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate PostgreSQL document ingestion and retrieval readiness.",
    )
    parser.add_argument("--title", required=True)
    parser.add_argument("--question", required=True)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--min-score", type=float, default=0.6)
    return parser


def print_validation_result(result: dict) -> None:
    print("PostgreSQL 文档入库验收完成。")
    print("是否通过：", result["passed"])
    print("失败原因：", result["failure_reason"])
    print("文档标题：", result["title"])
    print("测试问题：", result["question"])
    print("是否找到文档：", result["document_found"])
    print("chunks 数量：", result["chunk_count"])
    print("embeddings 数量：", result["embedding_count"])
    print("embedding 是否完整：", result["is_embedding_complete"])
    print("检索结果数量：", result["retrieval_count"])
    print("是否检索到目标文档：", result["retrieved_expected_document"])
    print("Top1 是否命中目标文档：", result["top1_matches_document"])

    top1_result = result["top1_result"]

    if top1_result is not None:
        print("Top1 文档：", top1_result["document_title"])
        print("Top1 片段：", top1_result["text"])
        print("Top1 分数：", top1_result["score"])


def main():
    if not is_postgresql_database(DATABASE_URL):
        print("DATABASE_URL 不是 PostgreSQL 地址，已停止。")
        print("当前 DATABASE_URL:", DATABASE_URL)
        return

    parser = build_argument_parser()
    args = parser.parse_args()

    with psycopg.connect(DATABASE_URL) as connection:
        result = validate_postgresql_document_ingestion(
            connection,
            title=args.title,
            question=args.question,
            top_k=args.top_k,
            min_score=args.min_score,
        )

    print_validation_result(result)


if __name__ == "__main__":
    main()
