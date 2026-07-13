import psycopg

from backend.config import DATABASE_URL
from backend.services.database_url_service import is_postgresql_database
from backend.services.postgresql_natural_language_search_service import (
    search_postgresql_chunks_by_question,
)


DEFAULT_QUESTIONS = [
    {
        "question": "员工每天需要工作多久？",
        "expected_text": "员工每天需要完成 8 小时工作。",
    },
    {
        "question": "差旅报销多久内提交？",
        "expected_text": "差旅报销需要在出差结束后 7 天内提交。",
    },
]

DEFAULT_MIN_SCORES = [0.0, 0.6, 0.8]


def evaluate_postgresql_retrieval(
    connection,
    questions: list[dict],
    top_k: int = 2,
    min_score: float = 0.0,
) -> dict:
    items = []
    passed_count = 0

    for item in questions:
        question = item["question"]
        expected_text = item["expected_text"]

        search_result = search_postgresql_chunks_by_question(
            connection,
            question=question,
            top_k=top_k,
            min_score=min_score,
        )

        results = search_result["results"]

        top_result_text = ""

        if len(results) > 0:
            top_result_text = results[0]["text"]

        found = False

        for result in results:
            if expected_text in result["text"]:
                found = True

        if found:
            passed_count = passed_count + 1

        items.append(
            {
                "question": question,
                "expected_text": expected_text,
                "passed": found,
                "top_result_text": top_result_text,
                "result_count": len(results),
            }
        )

    total = len(questions)

    hit_rate = 0.0

    if total > 0:
        hit_rate = passed_count / total

    return {
        "total": total,
        "passed": passed_count,
        "hit_rate": hit_rate,
        "top_k": top_k,
        "min_score": min_score,
        "items": items,
    }


def evaluate_postgresql_retrieval_for_min_scores(
    connection,
    questions: list[dict],
    top_k: int = 2,
    min_scores: list[float] | None = None,
) -> list[dict]:
    if min_scores is None:
        min_scores = DEFAULT_MIN_SCORES

    results = []

    for min_score in min_scores:
        result = evaluate_postgresql_retrieval(
            connection,
            questions=questions,
            top_k=top_k,
            min_score=min_score,
        )

        results.append(result)

    return results


def main():
    if not is_postgresql_database(DATABASE_URL):
        print("DATABASE_URL 不是 PostgreSQL 地址，已停止。")
        print("当前 DATABASE_URL:", DATABASE_URL)
        return

    with psycopg.connect(DATABASE_URL) as connection:
        results = evaluate_postgresql_retrieval_for_min_scores(
            connection,
            questions=DEFAULT_QUESTIONS,
            top_k=2,
        )

    print("PostgreSQL 检索评测完成。")

    for result in results:
        print("-" * 50)
        print("top_k：", result["top_k"])
        print("min_score：", result["min_score"])
        print("问题数量：", result["total"])
        print("通过数量：", result["passed"])
        print("命中率：", result["hit_rate"])

        for item in result["items"]:
            print("-" * 50)
            print("问题：", item["question"])
            print("期望片段：", item["expected_text"])
            print("Top1 片段：", item["top_result_text"])
            print("是否通过：", item["passed"])


if __name__ == "__main__":
    main()
