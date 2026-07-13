import psycopg

from backend.config import DATABASE_URL
from backend.services.database_url_service import is_postgresql_database
from backend.services.langgraph_agent import run_langgraph_agent
from backend.services.ollama_service import generate_with_ollama
from week10.evaluate_postgresql_migrated_document_agent import (
    contains_expected_document,
    top_item_matches_expected_document,
)


DEFAULT_BATCH_MIGRATION_AGENT_CASES = [
    {
        "question": "新员工什么时候完成安全培训？",
        "expected_title": "员工手册",
    },
    {
        "question": "请假需要怎么申请？",
        "expected_title": "请假制度",
    },
    {
        "question": "员工可以远程办公吗？",
        "expected_title": "远程办公制度",
    },
    {
        "question": "员工借用公司设备需要做什么？",
        "expected_title": "设备借用制度",
    },
    {
        "question": "访客进入办公区需要做什么？",
        "expected_title": "visitor_policy.txt",
    },
]


def evaluate_batch_migrated_document_case(case: dict, result: dict) -> dict:
    expected_title = case["expected_title"]
    snippets = result.get("snippets", [])
    citations = result.get("citations", [])

    retrieved_expected_document = contains_expected_document(
        snippets,
        expected_title,
    )
    cited_expected_document = contains_expected_document(
        citations,
        expected_title,
    )
    top_snippet_matched = top_item_matches_expected_document(
        snippets,
        expected_title,
    )
    top_citation_matched = top_item_matches_expected_document(
        citations,
        expected_title,
    )
    has_valid_context = result.get("has_valid_context") is True

    passed = has_valid_context and (
        retrieved_expected_document or cited_expected_document
    )

    return {
        "question": case["question"],
        "expected_title": expected_title,
        "passed": passed,
        "answer": result.get("answer", ""),
        "has_valid_context": has_valid_context,
        "is_fallback": result.get("is_fallback", False),
        "snippet_count": len(snippets),
        "citation_count": len(citations),
        "retrieved_expected_document": retrieved_expected_document,
        "cited_expected_document": cited_expected_document,
        "top_snippet_matched": top_snippet_matched,
        "top_citation_matched": top_citation_matched,
        "snippets": snippets,
        "citations": citations,
    }


def evaluate_postgresql_migrated_documents_batch(
    connection,
    cases: list[dict] | None = None,
    top_k: int = 3,
    min_score: float = 0.6,
    mode: str = "precomputed_embedding",
    timeout_seconds: float = 30,
    generator=generate_with_ollama,
) -> dict:
    if cases is None:
        cases = DEFAULT_BATCH_MIGRATION_AGENT_CASES

    items = []

    for case in cases:
        result = run_langgraph_agent(
            question=case["question"],
            top_k=top_k,
            mode=mode,
            min_score=min_score,
            timeout_seconds=timeout_seconds,
            retriever_backend="postgresql",
            postgresql_connection=connection,
            generator=generator,
        )

        items.append(
            evaluate_batch_migrated_document_case(
                case=case,
                result=result,
            )
        )

    passed_count = 0

    for item in items:
        if item["passed"]:
            passed_count = passed_count + 1

    return {
        "total": len(items),
        "passed": passed_count,
        "pass_rate": passed_count / len(items) if items else 0,
        "top_k": top_k,
        "min_score": min_score,
        "mode": mode,
        "retriever_backend": "postgresql",
        "items": items,
    }


def print_batch_evaluation_result(result: dict):
    print("PostgreSQL 批量迁移文档 Agent 验收完成。")
    print("问题数量：", result["total"])
    print("通过数量：", result["passed"])
    print("通过率：", result["pass_rate"])
    print("检索后端：", result["retriever_backend"])
    print("检索模式：", result["mode"])
    print("top_k：", result["top_k"])
    print("min_score：", result["min_score"])

    for item in result["items"]:
        print("-" * 50)
        print("问题：", item["question"])
        print("期望文档：", item["expected_title"])
        print("是否通过：", item["passed"])
        print("has_valid_context：", item["has_valid_context"])
        print("是否兜底回答：", item["is_fallback"])
        print("Top1 snippet 是否命中：", item["top_snippet_matched"])
        print("Top1 citation 是否命中：", item["top_citation_matched"])
        print("回答：", item["answer"])

        for index, citation in enumerate(item["citations"], start=1):
            print(f"[{index}] {citation['title']} - {citation['path']}")


def main():
    if not is_postgresql_database(DATABASE_URL):
        print("DATABASE_URL 不是 PostgreSQL 地址，已停止。")
        print("当前 DATABASE_URL:", DATABASE_URL)
        return

    with psycopg.connect(DATABASE_URL) as connection:
        result = evaluate_postgresql_migrated_documents_batch(connection)

    print_batch_evaluation_result(result)


if __name__ == "__main__":
    main()