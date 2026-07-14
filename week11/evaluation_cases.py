import json
from pathlib import Path


DEFAULT_EVALUATION_CASES_PATH = Path("docs/evaluations/rag-cases.json")

REQUIRED_FIELDS = {
    "id",
    "question",
    "expected_answer_type",
    "expected_document_title",
    "retriever_backend",
    "mode",
    "top_k",
    "min_score",
}

SUPPORTED_ANSWER_TYPES = {"answer", "refusal"}
SUPPORTED_RETRIEVER_BACKENDS = {"sqlite", "postgresql"}
SUPPORTED_MODES = {"keyword", "vector", "embedding", "precomputed_embedding"}


def validate_evaluation_case(case: dict) -> dict:
    missing_fields = REQUIRED_FIELDS - set(case)

    if missing_fields:
        fields = ", ".join(sorted(missing_fields))
        raise ValueError(f"Evaluation case is missing required fields: {fields}")

    for field in [
        "id",
        "question",
        "expected_answer_type",
        "retriever_backend",
        "mode",
    ]:
        if not isinstance(case[field], str) or case[field].strip() == "":
            raise ValueError(f"Evaluation case field must be a non-empty string: {field}")

    if not isinstance(case["expected_document_title"], str):
        raise ValueError("Evaluation case field must be a string: expected_document_title")

    if case["expected_answer_type"] not in SUPPORTED_ANSWER_TYPES:
        raise ValueError(
            f"Unsupported expected_answer_type: {case['expected_answer_type']}"
        )

    if case["retriever_backend"] not in SUPPORTED_RETRIEVER_BACKENDS:
        raise ValueError(f"Unsupported retriever_backend: {case['retriever_backend']}")

    if case["mode"] not in SUPPORTED_MODES:
        raise ValueError(f"Unsupported retrieval mode: {case['mode']}")

    if not isinstance(case["top_k"], int) or case["top_k"] < 1:
        raise ValueError("Evaluation case top_k must be an integer greater than 0.")

    if not isinstance(case["min_score"], int | float):
        raise ValueError("Evaluation case min_score must be a number.")

    if case["min_score"] < 0 or case["min_score"] > 1:
        raise ValueError("Evaluation case min_score must be between 0 and 1.")

    if (
        case["expected_answer_type"] == "answer"
        and case["expected_document_title"].strip() == ""
    ):
        raise ValueError("Answer evaluation cases must include expected_document_title.")

    return case


def load_evaluation_cases(
    file_path: str | Path = DEFAULT_EVALUATION_CASES_PATH,
) -> list[dict]:
    path = Path(file_path)
    cases = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(cases, list):
        raise ValueError("Evaluation cases file must contain a JSON list.")

    return [validate_evaluation_case(case) for case in cases]


def filter_evaluation_cases(
    cases: list[dict],
    retriever_backend: str | None = None,
    expected_answer_type: str | None = None,
) -> list[dict]:
    filtered_cases = cases

    if retriever_backend is not None:
        filtered_cases = [
            case
            for case in filtered_cases
            if case["retriever_backend"] == retriever_backend
        ]

    if expected_answer_type is not None:
        filtered_cases = [
            case
            for case in filtered_cases
            if case["expected_answer_type"] == expected_answer_type
        ]

    return filtered_cases


def to_agent_case(case: dict) -> dict:
    return {
        "id": case["id"],
        "question": case["question"],
        "case_type": case["expected_answer_type"],
        "expected_document_title": case["expected_document_title"],
    }


def load_agent_evaluation_cases(
    file_path: str | Path = DEFAULT_EVALUATION_CASES_PATH,
    retriever_backend: str | None = None,
) -> list[dict]:
    cases = load_evaluation_cases(file_path)
    cases = filter_evaluation_cases(cases, retriever_backend=retriever_backend)
    return [to_agent_case(case) for case in cases]


def summarize_evaluation_cases(cases: list[dict]) -> dict:
    summary = {
        "total": len(cases),
        "by_backend": {},
        "by_answer_type": {},
    }

    for case in cases:
        backend = case["retriever_backend"]
        answer_type = case["expected_answer_type"]

        summary["by_backend"][backend] = summary["by_backend"].get(backend, 0) + 1
        summary["by_answer_type"][answer_type] = (
            summary["by_answer_type"].get(answer_type, 0) + 1
        )

    return summary


def main():
    cases = load_evaluation_cases()
    summary = summarize_evaluation_cases(cases)

    print("RAG 评测集加载完成。")
    print("评测用例数量：", summary["total"])
    print("按检索后端统计：", summary["by_backend"])
    print("按回答类型统计：", summary["by_answer_type"])


if __name__ == "__main__":
    main()
