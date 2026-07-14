import argparse

from pathlib import Path
from typing import Callable

import psycopg

from backend.config import DATABASE_URL, SQLITE_ADMIN_DATABASE_PATH
from backend.services.database_url_service import is_postgresql_database
from backend.services.langgraph_agent import run_langgraph_agent
from backend.services.ollama_service import generate_with_ollama
from week11.evaluation_cases import (
    DEFAULT_EVALUATION_CASES_PATH,
    load_evaluation_cases,
    select_evaluation_cases,
)


DEFAULT_EVALUATION_REPORT_PATH = Path("docs/evaluations/rag-evaluation-run.md")


def is_expected_document_in_citations(case: dict, citations: list[dict]) -> bool:
    expected_document_title = case["expected_document_title"]

    if expected_document_title == "":
        return True

    for citation in citations:
        if citation.get("title") == expected_document_title:
            return True

    return False


def is_expected_document_in_snippets(case: dict, snippets: list[dict]) -> bool:
    expected_document_title = case["expected_document_title"]

    if expected_document_title == "":
        return True

    for snippet in snippets:
        if snippet.get("title") == expected_document_title:
            return True

    return False


def build_failure_reasons(
    expected_answer_type: str,
    answer: str,
    has_valid_context: bool,
    is_fallback: bool,
    is_timeout: bool,
    citations: list[dict],
    expected_document_in_citations: bool,
) -> list[str]:
    failure_reasons = []

    if expected_answer_type == "answer":
        if not has_valid_context:
            failure_reasons.append("invalid_context")

        if answer == "":
            failure_reasons.append("empty_answer")

        if is_fallback:
            failure_reasons.append("fallback_answer")

        if is_timeout:
            failure_reasons.append("timeout")

        if citations == []:
            failure_reasons.append("missing_citations")

        if not expected_document_in_citations:
            failure_reasons.append("expected_document_not_cited")

        return failure_reasons

    if expected_answer_type == "refusal":
        if has_valid_context:
            failure_reasons.append("unexpected_valid_context")

        if answer == "":
            failure_reasons.append("empty_answer")

        if is_fallback:
            failure_reasons.append("fallback_answer")

        if is_timeout:
            failure_reasons.append("timeout")

        if citations != []:
            failure_reasons.append("unexpected_citations_for_refusal")

        return failure_reasons

    raise ValueError(f"Unsupported expected_answer_type: {expected_answer_type}")


def build_failure_stages(
    failure_reasons: list[str],
    snippet_count: int,
    skipped: bool = False,
) -> list[str]:
    if skipped:
        return ["skipped"]

    stage_by_reason = {
        "empty_answer": "generation",
        "fallback_answer": "generation",
        "timeout": "timeout",
        "missing_citations": "citation",
        "expected_document_not_cited": "citation",
        "unexpected_valid_context": "validation",
        "unexpected_citations_for_refusal": "citation",
    }
    failure_stages = []

    for reason in failure_reasons:
        if reason == "invalid_context":
            if snippet_count == 0:
                stage = "retrieval"
            else:
                stage = "validation"
        else:
            stage = stage_by_reason.get(reason, "unknown")

        if stage not in failure_stages:
            failure_stages.append(stage)

    return failure_stages


def evaluate_rag_result(case: dict, result: dict) -> dict:
    citations = result.get("citations", [])
    snippets = result.get("snippets", [])
    answer = result.get("answer", "")
    has_valid_context = result.get("has_valid_context") is True
    is_fallback = result.get("is_fallback") is True
    fallback_reason = result.get("fallback_reason", "")
    is_timeout = result.get("is_timeout") is True
    expected_answer_type = case["expected_answer_type"]
    expected_document_in_citations = is_expected_document_in_citations(
        case,
        citations,
    )
    expected_document_in_snippets = is_expected_document_in_snippets(
        case,
        snippets,
    )

    failure_reasons = build_failure_reasons(
        expected_answer_type=expected_answer_type,
        answer=answer,
        has_valid_context=has_valid_context,
        is_fallback=is_fallback,
        is_timeout=is_timeout,
        citations=citations,
        expected_document_in_citations=expected_document_in_citations,
    )
    failure_stages = build_failure_stages(
        failure_reasons=failure_reasons,
        snippet_count=len(snippets),
    )

    return {
        "id": case["id"],
        "question": case["question"],
        "expected_answer_type": expected_answer_type,
        "expected_document_title": case["expected_document_title"],
        "scenario": case.get("scenario", ""),
        "tags": case.get("tags", []),
        "message_count": len(case.get("messages", [])),
        "retriever_backend": case["retriever_backend"],
        "mode": case["mode"],
        "top_k": case["top_k"],
        "min_score": case["min_score"],
        "passed": failure_reasons == [],
        "failure_reasons": failure_reasons,
        "failure_stages": failure_stages,
        "skipped": False,
        "skip_reason": "",
        "answer": answer,
        "has_valid_context": has_valid_context,
        "is_fallback": is_fallback,
        "fallback_reason": fallback_reason,
        "is_timeout": is_timeout,
        "citation_count": len(citations),
        "citations": citations,
        "snippet_count": len(snippets),
        "snippets": snippets,
        "expected_document_in_citations": expected_document_in_citations,
        "expected_document_in_snippets": expected_document_in_snippets,
    }


def build_skipped_evaluation_item(case: dict, reason: str) -> dict:
    return {
        "id": case["id"],
        "question": case["question"],
        "expected_answer_type": case["expected_answer_type"],
        "expected_document_title": case["expected_document_title"],
        "scenario": case.get("scenario", ""),
        "tags": case.get("tags", []),
        "message_count": len(case.get("messages", [])),
        "retriever_backend": case["retriever_backend"],
        "mode": case["mode"],
        "top_k": case["top_k"],
        "min_score": case["min_score"],
        "passed": False,
        "failure_reasons": [],
        "failure_stages": ["skipped"],
        "skipped": True,
        "skip_reason": reason,
        "answer": "",
        "has_valid_context": False,
        "is_fallback": False,
        "fallback_reason": "",
        "is_timeout": False,
        "citation_count": 0,
        "citations": [],
        "snippet_count": 0,
        "snippets": [],
        "expected_document_in_citations": False,
        "expected_document_in_snippets": False,
    }


def run_langgraph_evaluation_case(
    case: dict,
    postgresql_connection=None,
    generator: Callable[[str], str] = generate_with_ollama,
) -> dict:
    return run_langgraph_agent(
        question=case["question"],
        database_path=SQLITE_ADMIN_DATABASE_PATH,
        messages=case.get("messages", []),
        top_k=case["top_k"],
        mode=case["mode"],
        min_score=case["min_score"],
        retriever_backend=case["retriever_backend"],
        postgresql_connection=postgresql_connection,
        generator=generator,
    )


def summarize_rag_evaluation(items: list[dict]) -> dict:
    evaluated_items = [item for item in items if not item["skipped"]]
    passed_items = [item for item in evaluated_items if item["passed"]]
    failed_items = [item for item in evaluated_items if not item["passed"]]
    skipped_items = [item for item in items if item["skipped"]]
    by_backend = {}
    by_answer_type = {}
    by_scenario = {}
    by_tag = {}

    for item in items:
        backend = item["retriever_backend"]
        answer_type = item["expected_answer_type"]
        scenario = item["scenario"]

        if backend not in by_backend:
            by_backend[backend] = {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
            }

        if answer_type not in by_answer_type:
            by_answer_type[answer_type] = {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
            }

        if scenario not in by_scenario:
            by_scenario[scenario] = {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
            }

        for tag in item["tags"]:
            if tag not in by_tag:
                by_tag[tag] = {
                    "total": 0,
                    "passed": 0,
                    "failed": 0,
                    "skipped": 0,
                }

        by_backend[backend]["total"] = by_backend[backend]["total"] + 1
        by_answer_type[answer_type]["total"] = by_answer_type[answer_type]["total"] + 1
        by_scenario[scenario]["total"] = by_scenario[scenario]["total"] + 1

        for tag in item["tags"]:
            by_tag[tag]["total"] = by_tag[tag]["total"] + 1

        if item["skipped"]:
            by_backend[backend]["skipped"] = by_backend[backend]["skipped"] + 1
            by_answer_type[answer_type]["skipped"] = (
                by_answer_type[answer_type]["skipped"] + 1
            )
            by_scenario[scenario]["skipped"] = by_scenario[scenario]["skipped"] + 1

            for tag in item["tags"]:
                by_tag[tag]["skipped"] = by_tag[tag]["skipped"] + 1
        elif item["passed"]:
            by_backend[backend]["passed"] = by_backend[backend]["passed"] + 1
            by_answer_type[answer_type]["passed"] = (
                by_answer_type[answer_type]["passed"] + 1
            )
            by_scenario[scenario]["passed"] = by_scenario[scenario]["passed"] + 1

            for tag in item["tags"]:
                by_tag[tag]["passed"] = by_tag[tag]["passed"] + 1
        else:
            by_backend[backend]["failed"] = by_backend[backend]["failed"] + 1
            by_answer_type[answer_type]["failed"] = (
                by_answer_type[answer_type]["failed"] + 1
            )
            by_scenario[scenario]["failed"] = by_scenario[scenario]["failed"] + 1

            for tag in item["tags"]:
                by_tag[tag]["failed"] = by_tag[tag]["failed"] + 1

    evaluated_count = len(evaluated_items)

    return {
        "total": len(items),
        "evaluated": evaluated_count,
        "passed": len(passed_items),
        "failed": len(failed_items),
        "skipped": len(skipped_items),
        "pass_rate": len(passed_items) / evaluated_count if evaluated_count else 0,
        "by_backend": by_backend,
        "by_answer_type": by_answer_type,
        "by_scenario": by_scenario,
        "by_tag": by_tag,
    }


def run_rag_evaluation(
    cases: list[dict] | None = None,
    runner: Callable[..., dict] | None = None,
    postgresql_connection=None,
    generator: Callable[[str], str] = generate_with_ollama,
    retriever_backend: str | None = None,
    expected_answer_type: str | None = None,
    scenario: str | None = None,
    tags: str | list[str] | tuple[str, ...] | set[str] | None = None,
    mode: str | None = None,
    tag_match: str = "all",
) -> dict:
    if cases is None:
        cases = load_evaluation_cases()

    cases = select_evaluation_cases(
        cases=cases,
        retriever_backend=retriever_backend,
        expected_answer_type=expected_answer_type,
        scenario=scenario,
        tags=tags,
        mode=mode,
        tag_match=tag_match,
    )

    actual_runner = runner if runner is not None else run_langgraph_evaluation_case
    items = []

    for case in cases:
        if (
            runner is None
            and case["retriever_backend"] == "postgresql"
            and postgresql_connection is None
        ):
            item = build_skipped_evaluation_item(
                case,
                reason="postgresql_connection_not_configured",
            )
        else:
            result = actual_runner(
                case=case,
                postgresql_connection=postgresql_connection,
                generator=generator,
            )
            item = evaluate_rag_result(case, result)

        items.append(item)

    summary = summarize_rag_evaluation(items)

    return {
        **summary,
        "items": items,
    }


def format_bool(value: bool) -> str:
    return "是" if value else "否"


def build_rag_evaluation_report(evaluation: dict) -> str:
    lines = [
        "# RAG 统一评测报告",
        "",
        f"- 总用例数：{evaluation['total']}",
        f"- 实际执行数：{evaluation['evaluated']}",
        f"- 通过数：{evaluation['passed']}",
        f"- 失败数：{evaluation['failed']}",
        f"- 跳过数：{evaluation['skipped']}",
        f"- 通过率：{evaluation['pass_rate']}",
        "",
        "## 按检索后端统计",
        "",
    ]

    for backend, summary in evaluation["by_backend"].items():
        lines.append(
            f"- {backend}：total={summary['total']}，passed={summary['passed']}，"
            f"failed={summary['failed']}，skipped={summary['skipped']}"
        )

    lines.extend(
        [
            "",
            "## 按回答类型统计",
            "",
        ]
    )

    for answer_type, summary in evaluation["by_answer_type"].items():
        lines.append(
            f"- {answer_type}：total={summary['total']}，passed={summary['passed']}，"
            f"failed={summary['failed']}，skipped={summary['skipped']}"
        )

    lines.extend(
        [
            "",
            "## 按场景统计",
            "",
        ]
    )

    for scenario, summary in evaluation["by_scenario"].items():
        lines.append(
            f"- {scenario}：total={summary['total']}，passed={summary['passed']}，"
            f"failed={summary['failed']}，skipped={summary['skipped']}"
        )

    lines.extend(
        [
            "",
            "## 按标签统计",
            "",
        ]
    )

    for tag, summary in evaluation["by_tag"].items():
        lines.append(
            f"- {tag}：total={summary['total']}，passed={summary['passed']}，"
            f"failed={summary['failed']}，skipped={summary['skipped']}"
        )

    lines.extend(
        [
            "",
            "## 明细",
            "",
        ]
    )

    for item in evaluation["items"]:
        lines.extend(
            [
                f"### {item['id']}",
                "",
                f"- 问题：{item['question']}",
                f"- 期望类型：{item['expected_answer_type']}",
                f"- 期望文档：{item['expected_document_title']}",
                f"- 场景：{item['scenario']}",
                f"- 标签：{', '.join(item['tags'])}",
                f"- 历史消息数量：{item['message_count']}",
                f"- 检索后端：{item['retriever_backend']}",
                f"- 检索模式：{item['mode']}",
                f"- top_k：{item['top_k']}",
                f"- min_score：{item['min_score']}",
                f"- 是否通过：{format_bool(item['passed'])}",
                f"- 失败原因：{', '.join(item['failure_reasons']) if item['failure_reasons'] else '无'}",
                f"- 失败阶段：{', '.join(item['failure_stages']) if item['failure_stages'] else '无'}",
                f"- 是否跳过：{format_bool(item['skipped'])}",
                f"- 跳过原因：{item['skip_reason']}",
                f"- has_valid_context：{format_bool(item['has_valid_context'])}",
                f"- 是否兜底回答：{format_bool(item['is_fallback'])}",
                f"- 兜底原因：{item['fallback_reason'] if item['fallback_reason'] else '无'}",
                f"- 是否超时：{format_bool(item['is_timeout'])}",
                f"- 引用数量：{item['citation_count']}",
                f"- snippets 数量：{item['snippet_count']}",
                f"- 期望文档是否出现在引用中：{format_bool(item['expected_document_in_citations'])}",
                f"- 期望文档是否出现在 snippets 中：{format_bool(item['expected_document_in_snippets'])}",
                "",
                "回答：",
                "",
                item["answer"],
                "",
                "引用：",
                "",
            ]
        )

        if item["citations"] == []:
            lines.append("- 无")
        else:
            for index, citation in enumerate(item["citations"], start=1):
                lines.append(
                    f"- [{index}] {citation.get('title', '')} - {citation.get('path', '')}"
                )

        lines.append("")

    return "\n".join(lines)


def write_rag_evaluation_report(
    evaluation: dict,
    report_path: str | Path = DEFAULT_EVALUATION_REPORT_PATH,
) -> Path:
    path = Path(report_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_rag_evaluation_report(evaluation), encoding="utf-8")
    return path


def parse_rag_evaluation_args(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Run shared RAG evaluation cases and write a Markdown report."
    )
    parser.add_argument(
        "--case-file",
        default=str(DEFAULT_EVALUATION_CASES_PATH),
        help="Path to the evaluation cases JSON file.",
    )
    parser.add_argument(
        "--report-path",
        default=str(DEFAULT_EVALUATION_REPORT_PATH),
        help="Path to the generated Markdown report.",
    )
    parser.add_argument(
        "--retriever-backend",
        help="Only run cases for this retriever backend.",
    )
    parser.add_argument(
        "--expected-answer-type",
        help="Only run cases with this expected answer type.",
    )
    parser.add_argument(
        "--scenario",
        help="Only run cases for this scenario.",
    )
    parser.add_argument(
        "--tag",
        action="append",
        dest="tags",
        help="Only run cases with this tag. Can be provided multiple times.",
    )
    parser.add_argument(
        "--tag-match",
        choices=["all", "any"],
        default="all",
        help="When multiple tags are provided, require all tags or any tag.",
    )
    parser.add_argument(
        "--mode",
        help="Only run cases for this retrieval mode.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None):
    args = parse_rag_evaluation_args(argv)
    cases = load_evaluation_cases(args.case_file)
    postgresql_connection = None

    try:
        if is_postgresql_database(DATABASE_URL):
            postgresql_connection = psycopg.connect(DATABASE_URL)

        evaluation = run_rag_evaluation(
            cases=cases,
            postgresql_connection=postgresql_connection,
            retriever_backend=args.retriever_backend,
            expected_answer_type=args.expected_answer_type,
            scenario=args.scenario,
            tags=args.tags,
            mode=args.mode,
            tag_match=args.tag_match,
        )
        report_path = write_rag_evaluation_report(evaluation, args.report_path)

        print("RAG 统一评测完成。")
        print("总用例数：", evaluation["total"])
        print("实际执行数：", evaluation["evaluated"])
        print("通过数：", evaluation["passed"])
        print("失败数：", evaluation["failed"])
        print("跳过数：", evaluation["skipped"])
        print("通过率：", evaluation["pass_rate"])
        print("评测报告已保存：", report_path)
    finally:
        if postgresql_connection is not None:
            postgresql_connection.close()


if __name__ == "__main__":
    main()
