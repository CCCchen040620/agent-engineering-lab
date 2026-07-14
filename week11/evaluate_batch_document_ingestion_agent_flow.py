import argparse
import json
from pathlib import Path

import psycopg

from backend.config import DATABASE_URL
from backend.services.database_url_service import is_postgresql_database
from backend.services.ollama_service import generate_with_ollama
from week11.evaluate_document_ingestion_agent_flow import (
    build_document_ingestion_agent_report,
    evaluate_document_ingestion_agent_flow,
    format_bool,
)


DEFAULT_BATCH_DOCUMENT_INGESTION_AGENT_CASES_PATH = Path(
    "docs/evaluations/document-ingestion-agent-cases.json"
)
DEFAULT_BATCH_DOCUMENT_INGESTION_AGENT_REPORT_PATH = Path(
    ".local/evaluations/document-ingestion-agent-batch-run.md"
)

REQUIRED_BATCH_CASE_FIELDS = {"id", "title", "question"}
SUPPORTED_BATCH_MODES = {"keyword", "vector", "embedding", "precomputed_embedding"}
RETRIEVAL_ONLY_GENERATION_FAILURE_REASON = "generation_skipped"


def generate_retrieval_only_answer(prompt: str) -> str:
    return "Retrieval-only batch validation skipped local LLM generation."


def validate_batch_document_ingestion_agent_case(case: dict) -> dict:
    case = {**case}
    missing_fields = REQUIRED_BATCH_CASE_FIELDS - set(case)

    if missing_fields:
        fields = ", ".join(sorted(missing_fields))
        raise ValueError(f"Batch document ingestion case is missing fields: {fields}")

    for field in ["id", "title", "question"]:
        if not isinstance(case[field], str) or case[field].strip() == "":
            raise ValueError(f"Batch document ingestion case field is invalid: {field}")

    if "source" not in case:
        case["source"] = "migration"

    if not isinstance(case["source"], str) or case["source"].strip() == "":
        raise ValueError("Batch document ingestion case source must be non-empty.")

    if "mode" not in case:
        case["mode"] = "precomputed_embedding"

    if case["mode"] not in SUPPORTED_BATCH_MODES:
        raise ValueError(f"Unsupported batch document ingestion mode: {case['mode']}")

    if "top_k" not in case:
        case["top_k"] = 3

    if not isinstance(case["top_k"], int) or case["top_k"] < 1:
        raise ValueError("Batch document ingestion case top_k must be greater than 0.")

    if "min_score" not in case:
        case["min_score"] = 0.6

    if not isinstance(case["min_score"], int | float):
        raise ValueError("Batch document ingestion case min_score must be a number.")

    if case["min_score"] < 0 or case["min_score"] > 1:
        raise ValueError("Batch document ingestion case min_score must be 0 to 1.")

    return case


def load_batch_document_ingestion_agent_cases(
    case_file: str | Path = DEFAULT_BATCH_DOCUMENT_INGESTION_AGENT_CASES_PATH,
) -> list[dict]:
    path = Path(case_file)
    cases = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(cases, list):
        raise ValueError("Batch document ingestion cases file must contain a JSON list.")

    return [validate_batch_document_ingestion_agent_case(case) for case in cases]


def evaluate_batch_document_ingestion_agent_case(
    connection,
    case: dict,
    timeout_seconds: float = 30,
    generator=generate_with_ollama,
    retrieval_only: bool = False,
    evaluator=evaluate_document_ingestion_agent_flow,
) -> dict:
    selected_generator = generate_retrieval_only_answer if retrieval_only else generator

    result = evaluator(
        connection,
        title=case["title"],
        question=case["question"],
        top_k=case["top_k"],
        min_score=case["min_score"],
        mode=case["mode"],
        timeout_seconds=timeout_seconds,
        generator=selected_generator,
    )

    if retrieval_only:
        result = {
            **result,
            "generation_skipped": True,
        }

        if result.get("retrieval_passed") is True:
            result["generation_passed"] = False
            result[
                "generation_failure_reason"
            ] = RETRIEVAL_ONLY_GENERATION_FAILURE_REASON
    else:
        result = {
            **result,
            "generation_skipped": False,
        }

    document = result.get("document")
    document_source = document.get("source", "") if document is not None else ""
    source_matched = document_source == case["source"]
    passed = result["passed"] and source_matched

    if not source_matched and result["failure_reason"] == "":
        failure_reason = "source_mismatch"
    else:
        failure_reason = result["failure_reason"]

    return {
        "case_id": case["id"],
        "expected_source": case["source"],
        "document_source": document_source,
        "source_matched": source_matched,
        **result,
        "passed": passed,
        "failure_reason": failure_reason,
    }


def evaluate_batch_document_ingestion_agent_flow(
    connection,
    cases: list[dict],
    timeout_seconds: float = 30,
    generator=generate_with_ollama,
    retrieval_only: bool = False,
    evaluator=evaluate_document_ingestion_agent_flow,
) -> dict:
    validated_cases = [
        validate_batch_document_ingestion_agent_case(case) for case in cases
    ]
    items = [
        evaluate_batch_document_ingestion_agent_case(
            connection=connection,
            case=case,
            timeout_seconds=timeout_seconds,
            generator=generator,
            retrieval_only=retrieval_only,
            evaluator=evaluator,
        )
        for case in validated_cases
    ]

    passed_count = sum(1 for item in items if item["passed"])
    retrieval_passed_count = sum(1 for item in items if item["retrieval_passed"])
    generation_passed_count = sum(
        1
        for item in items
        if item["generation_skipped"] is not True and item["generation_passed"]
    )
    generation_skipped_count = sum(1 for item in items if item["generation_skipped"])
    source_matched_count = sum(1 for item in items if item["source_matched"])

    return {
        "total": len(items),
        "passed": passed_count,
        "failed": len(items) - passed_count,
        "pass_rate": passed_count / len(items) if items else 0,
        "retrieval_passed": retrieval_passed_count,
        "generation_passed": generation_passed_count,
        "generation_skipped": generation_skipped_count,
        "source_matched": source_matched_count,
        "retriever_backend": "postgresql",
        "retrieval_only": retrieval_only,
        "items": items,
    }


def build_batch_document_ingestion_agent_report(evaluation: dict) -> str:
    lines = [
        "# PostgreSQL 批量文档入库 Agent 验收报告",
        "",
        "## 汇总",
        "",
        f"- 总用例数：{evaluation['total']}",
        f"- 通过数：{evaluation['passed']}",
        f"- 失败数：{evaluation['failed']}",
        f"- 通过率：{evaluation['pass_rate']}",
        f"- 检索层通过数：{evaluation['retrieval_passed']}",
        f"- 生成层通过数：{evaluation['generation_passed']}",
        f"- 生成层跳过数：{evaluation['generation_skipped']}",
        f"- source 匹配数：{evaluation['source_matched']}",
        f"- 检索后端：{evaluation['retriever_backend']}",
        f"- 是否仅验证检索层：{format_bool(evaluation['retrieval_only'])}",
        "",
        "## 明细",
        "",
    ]

    if evaluation["items"] == []:
        lines.append("无用例。")
    else:
        for item in evaluation["items"]:
            lines.extend(
                [
                    f"### {item['case_id']}",
                    "",
                    f"- 是否通过：{format_bool(item['passed'])}",
                    f"- 失败原因：{item['failure_reason']}",
                    f"- 文档标题：{item['title']}",
                    f"- 问题：{item['question']}",
                    f"- 期望 source：{item['expected_source']}",
                    f"- 实际 source：{item['document_source']}",
                    f"- source 是否匹配：{format_bool(item['source_matched'])}",
                    f"- 检索层是否通过：{format_bool(item['retrieval_passed'])}",
                    f"- 生成层是否通过：{format_bool(item['generation_passed'])}",
                    f"- 生成层是否跳过：{format_bool(item['generation_skipped'])}",
                    f"- 引用数量：{item['citation_count']}",
                    "",
                ]
            )
            lines.append(build_document_ingestion_agent_report(item))
            lines.append("")

    return "\n".join(lines)


def write_batch_document_ingestion_agent_report(
    evaluation: dict,
    report_path: str | Path = DEFAULT_BATCH_DOCUMENT_INGESTION_AGENT_REPORT_PATH,
) -> Path:
    path = Path(report_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        build_batch_document_ingestion_agent_report(evaluation),
        encoding="utf-8",
    )
    return path


def print_batch_document_ingestion_agent_result(evaluation: dict) -> None:
    print("PostgreSQL 批量文档入库 Agent 验收完成。")
    print("总用例数：", evaluation["total"])
    print("通过数：", evaluation["passed"])
    print("失败数：", evaluation["failed"])
    print("通过率：", evaluation["pass_rate"])
    print("检索层通过数：", evaluation["retrieval_passed"])
    print("生成层通过数：", evaluation["generation_passed"])
    print("生成层跳过数：", evaluation["generation_skipped"])
    print("source 匹配数：", evaluation["source_matched"])
    print("是否仅验证检索层：", evaluation["retrieval_only"])

    for item in evaluation["items"]:
        print("-" * 50)
        print("用例：", item["case_id"])
        print("文档标题：", item["title"])
        print("问题：", item["question"])
        print("是否通过：", item["passed"])
        print("失败原因：", item["failure_reason"])
        print("检索层是否通过：", item["retrieval_passed"])
        print("生成层是否通过：", item["generation_passed"])
        print("生成层是否跳过：", item["generation_skipped"])


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate multiple ingested PostgreSQL documents through the Agent.",
    )
    parser.add_argument(
        "--case-file",
        default=str(DEFAULT_BATCH_DOCUMENT_INGESTION_AGENT_CASES_PATH),
    )
    parser.add_argument(
        "--report-path",
        default=str(DEFAULT_BATCH_DOCUMENT_INGESTION_AGENT_REPORT_PATH),
    )
    parser.add_argument("--timeout-seconds", type=float, default=30)
    parser.add_argument(
        "--retrieval-only",
        action="store_true",
        help="Skip local LLM generation and validate retrieval/source/citations only.",
    )
    return parser


def main() -> None:
    if not is_postgresql_database(DATABASE_URL):
        print("DATABASE_URL 不是 PostgreSQL 地址，已停止。")
        print("当前 DATABASE_URL:", DATABASE_URL)
        raise SystemExit(1)

    parser = build_argument_parser()
    args = parser.parse_args()
    cases = load_batch_document_ingestion_agent_cases(args.case_file)

    with psycopg.connect(DATABASE_URL) as connection:
        evaluation = evaluate_batch_document_ingestion_agent_flow(
            connection,
            cases=cases,
            timeout_seconds=args.timeout_seconds,
            retrieval_only=args.retrieval_only,
        )

    print_batch_document_ingestion_agent_result(evaluation)
    report_path = write_batch_document_ingestion_agent_report(
        evaluation,
        args.report_path,
    )
    print("验收报告已保存：", report_path)

    if evaluation["passed"] != evaluation["total"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
