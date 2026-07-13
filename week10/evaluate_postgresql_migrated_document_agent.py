import psycopg

from backend.config import DATABASE_URL
from backend.services.database_url_service import is_postgresql_database
from backend.services.langgraph_agent import run_langgraph_agent
from backend.services.ollama_service import generate_with_ollama
from week10.seed_sqlite_migration_sample import SQLITE_MIGRATION_SAMPLE_TITLE


MIGRATED_DOCUMENT_QUESTION = "SQLite 迁移测试片段一是什么？"


def is_postgresql_snippet(snippet: dict) -> bool:
    return snippet.get("path", "").startswith("postgresql://chunk/")


def is_expected_document_item(item: dict, expected_title: str) -> bool:
    return item.get("title") == expected_title and is_postgresql_snippet(item)


def contains_expected_document(items: list[dict], expected_title: str) -> bool:
    for item in items:
        if is_expected_document_item(item, expected_title):
            return True

    return False


def top_item_matches_expected_document(
    items: list[dict],
    expected_title: str,
) -> bool:
    if items == []:
        return False

    return is_expected_document_item(items[0], expected_title)


def evaluate_migrated_document_agent_result(
    result: dict,
    expected_title: str,
) -> dict:
    snippets = result.get("snippets", [])
    citations = result.get("citations", [])

    retrieved_expected_document = contains_expected_document(snippets, expected_title)
    cited_expected_document = contains_expected_document(citations, expected_title)
    top_snippet_matched = top_item_matches_expected_document(snippets, expected_title)
    top_citation_matched = top_item_matches_expected_document(citations, expected_title)
    has_valid_context = result.get("has_valid_context") is True

    passed = has_valid_context and (top_snippet_matched or top_citation_matched)

    return {
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


def evaluate_postgresql_migrated_document_agent(
    connection,
    question: str = MIGRATED_DOCUMENT_QUESTION,
    expected_title: str = SQLITE_MIGRATION_SAMPLE_TITLE,
    top_k: int = 3,
    min_score: float = 0.6,
    mode: str = "precomputed_embedding",
    timeout_seconds: float = 30,
    generator=generate_with_ollama,
) -> dict:
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

    evaluation = evaluate_migrated_document_agent_result(
        agent_result,
        expected_title=expected_title,
    )

    return {
        "question": question,
        "expected_title": expected_title,
        "top_k": top_k,
        "min_score": min_score,
        "mode": mode,
        "retriever_backend": "postgresql",
        **evaluation,
    }


def print_evaluation_result(result: dict):
    print("PostgreSQL 迁移文档 Agent 验收完成。")
    print("是否通过：", result["passed"])
    print("问题：", result["question"])
    print("期望文档：", result["expected_title"])
    print("检索后端：", result["retriever_backend"])
    print("检索模式：", result["mode"])
    print("top_k：", result["top_k"])
    print("min_score：", result["min_score"])
    print("has_valid_context：", result["has_valid_context"])
    print("是否兜底回答：", result["is_fallback"])
    print("是否检索到期望文档：", result["retrieved_expected_document"])
    print("是否引用期望文档：", result["cited_expected_document"])
    print("Top1 snippet 是否为期望文档：", result["top_snippet_matched"])
    print("Top1 citation 是否为期望文档：", result["top_citation_matched"])
    print("snippets 数量：", result["snippet_count"])
    print("引用数量：", result["citation_count"])
    print("回答：", result["answer"])

    for index, snippet in enumerate(result["snippets"], start=1):
        print(f"snippet[{index}] {snippet['title']} - {snippet['path']}")

    for index, citation in enumerate(result["citations"], start=1):
        print(f"citation[{index}] {citation['title']} - {citation['path']}")


def main():
    if not is_postgresql_database(DATABASE_URL):
        print("DATABASE_URL 不是 PostgreSQL 地址，已停止。")
        print("当前 DATABASE_URL:", DATABASE_URL)
        return

    with psycopg.connect(DATABASE_URL) as connection:
        result = evaluate_postgresql_migrated_document_agent(connection)

    print_evaluation_result(result)


if __name__ == "__main__":
    main()
