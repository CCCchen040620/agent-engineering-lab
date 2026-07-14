from pathlib import Path
from typing import Callable

import psycopg

from backend.config import DATABASE_URL, SQLITE_ADMIN_DATABASE_PATH
from backend.services.database_url_service import is_postgresql_database
from backend.services.langgraph_agent import run_langgraph_agent
from backend.services.ollama_service import generate_with_ollama
from week11.evaluation_cases import load_evaluation_cases


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


def evaluate_rag_result(case: dict, result: dict) -> dict:
    citations = result.get("citations", [])
    snippets = result.get("snippets", [])
    answer = result.get("answer", "")
    has_valid_context = result.get("has_valid_context") is True
    is_fallback = result.get("is_fallback") is True
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

    if expected_answer_type == "answer":
        passed = (
            has_valid_context
            and answer != ""
            and not is_fallback
            and not is_timeout
            and len(citations) > 0
            and expected_document_in_citations
        )
    elif expected_answer_type == "refusal":
        passed = (
            not has_valid_context
            and answer != ""
            and not is_timeout
            and citations == []
        )
    else:
        raise ValueError(f"Unsupported expected_answer_type: {expected_answer_type}")

    return {
        "id": case["id"],
        "question": case["question"],
        "expected_answer_type": expected_answer_type,
        "expected_document_title": case["expected_document_title"],
        "scenario": case.get("scenario", ""),
        "tags": case.get("tags", []),
        "retriever_backend": case["retriever_backend"],
        "mode": case["mode"],
        "top_k": case["top_k"],
        "min_score": case["min_score"],
        "passed": passed,
        "skipped": False,
        "skip_reason": "",
        "answer": answer,
        "has_valid_context": has_valid_context,
        "is_fallback": is_fallback,
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
        "retriever_backend": case["retriever_backend"],
        "mode": case["mode"],
        "top_k": case["top_k"],
        "min_score": case["min_score"],
        "passed": False,
        "skipped": True,
        "skip_reason": reason,
        "answer": "",
        "has_valid_context": False,
        "is_fallback": False,
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
) -> dict:
    if cases is None:
        cases = load_evaluation_cases()

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
                f"- 检索后端：{item['retriever_backend']}",
                f"- 检索模式：{item['mode']}",
                f"- top_k：{item['top_k']}",
                f"- min_score：{item['min_score']}",
                f"- 是否通过：{format_bool(item['passed'])}",
                f"- 是否跳过：{format_bool(item['skipped'])}",
                f"- 跳过原因：{item['skip_reason']}",
                f"- has_valid_context：{format_bool(item['has_valid_context'])}",
                f"- 是否兜底回答：{format_bool(item['is_fallback'])}",
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


def main():
    cases = load_evaluation_cases()
    postgresql_connection = None

    try:
        if is_postgresql_database(DATABASE_URL):
            postgresql_connection = psycopg.connect(DATABASE_URL)

        evaluation = run_rag_evaluation(
            cases=cases,
            postgresql_connection=postgresql_connection,
        )
        report_path = write_rag_evaluation_report(evaluation)

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
