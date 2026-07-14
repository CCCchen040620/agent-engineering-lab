import psycopg

from backend.config import DATABASE_URL
from backend.services.database_url_service import is_postgresql_database
from backend.services.langgraph_agent import run_langgraph_agent
from backend.services.ollama_service import generate_with_ollama
from week11.evaluation_cases import load_agent_evaluation_cases


def get_default_agent_cases() -> list[dict]:
    return load_agent_evaluation_cases(retriever_backend="postgresql")


def is_postgresql_citation(citation: dict) -> bool:
    return citation.get("path", "").startswith("postgresql://chunk/")


def evaluate_agent_case(case: dict, result: dict) -> dict:
    citations = result.get("citations", [])
    has_valid_context = result.get("has_valid_context") is True
    answer = result.get("answer", "")
    case_type = case["case_type"]

    if case_type == "answer":
        passed = (
            has_valid_context
            and answer != ""
            and result.get("is_fallback") is False
            and len(citations) > 0
            and all(is_postgresql_citation(citation) for citation in citations)
        )
    elif case_type == "refusal":
        passed = (
            has_valid_context is False
            and "暂时无法回答" in answer
            and citations == []
        )
    else:
        raise ValueError(f"不支持的评测类型：{case_type}")

    return {
        "question": case["question"],
        "case_type": case_type,
        "passed": passed,
        "answer": answer,
        "has_valid_context": has_valid_context,
        "is_fallback": result.get("is_fallback", False),
        "citation_count": len(citations),
        "citations": citations,
    }


def evaluate_postgresql_agent(
    connection,
    cases: list[dict] | None = None,
    top_k: int = 2,
    min_score: float = 0.8,
    mode: str = "precomputed_embedding",
    timeout_seconds: float = 30,
    generator=generate_with_ollama,
) -> dict:
    if cases is None:
        cases = get_default_agent_cases()

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

        items.append(evaluate_agent_case(case, result))

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


def main():
    if not is_postgresql_database(DATABASE_URL):
        print("DATABASE_URL 不是 PostgreSQL 地址，已停止。")
        print("当前 DATABASE_URL:", DATABASE_URL)
        return

    with psycopg.connect(DATABASE_URL) as connection:
        result = evaluate_postgresql_agent(
            connection,
            top_k=2,
            min_score=0.8,
        )

    print("PostgreSQL LangGraph Agent 业务验收完成。")
    print("检索后端：", result["retriever_backend"])
    print("检索模式：", result["mode"])
    print("top_k：", result["top_k"])
    print("min_score：", result["min_score"])
    print("问题数量：", result["total"])
    print("通过数量：", result["passed"])
    print("通过率：", result["pass_rate"])

    for item in result["items"]:
        print("-" * 50)
        print("问题：", item["question"])
        print("类型：", item["case_type"])
        print("是否通过：", item["passed"])
        print("has_valid_context：", item["has_valid_context"])
        print("是否兜底回答：", item["is_fallback"])
        print("引用数量：", item["citation_count"])
        print("回答：", item["answer"])

        for index, citation in enumerate(item["citations"], start=1):
            print(f"[{index}] {citation['title']} - {citation['path']}")


if __name__ == "__main__":
    main()
