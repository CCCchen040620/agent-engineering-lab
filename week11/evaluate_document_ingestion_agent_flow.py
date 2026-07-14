import argparse
from pathlib import Path

import psycopg

from backend.config import DATABASE_URL
from backend.services.database_url_service import is_postgresql_database
from backend.services.langgraph_agent import run_langgraph_agent
from backend.services.ollama_service import generate_with_ollama
from backend.services.postgresql_document_repository import (
    find_document_by_title_from_postgresql,
)
from week10.evaluate_postgresql_agent import is_postgresql_citation


DEFAULT_DOCUMENT_INGESTION_AGENT_REPORT_PATH = Path(
    "docs/evaluations/document-ingestion-agent-run.md"
)


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


def get_retrieval_failure_reason(result: dict, title: str) -> str:
    citations = result.get("citations", [])

    if result.get("has_valid_context") is not True:
        return "invalid_context"

    if not citations_include_document(citations, title):
        return "expected_document_not_cited"

    if not top_citation_matches_document(citations, title):
        return "top_citation_mismatch"

    return ""


def get_generation_failure_reason(result: dict) -> str:
    answer = result.get("answer", "")

    if result.get("is_fallback") is True:
        return "fallback_answer"

    if answer_is_refusal(answer):
        return "refusal_answer"

    return ""


def get_agent_flow_failure_reason(result: dict, title: str) -> str:
    retrieval_failure_reason = get_retrieval_failure_reason(result, title)

    if retrieval_failure_reason != "":
        return retrieval_failure_reason

    return get_generation_failure_reason(result)


def evaluate_agent_result_for_document(result: dict, title: str) -> dict:
    citations = result.get("citations", [])
    retrieval_failure_reason = get_retrieval_failure_reason(result, title)
    generation_failure_reason = get_generation_failure_reason(result)
    failure_reason = (
        retrieval_failure_reason
        if retrieval_failure_reason != ""
        else generation_failure_reason
    )
    retrieval_passed = retrieval_failure_reason == ""
    generation_passed = generation_failure_reason == ""

    return {
        "passed": retrieval_passed,
        "failure_reason": failure_reason,
        "retrieval_passed": retrieval_passed,
        "retrieval_failure_reason": retrieval_failure_reason,
        "generation_passed": generation_passed,
        "generation_failure_reason": generation_failure_reason,
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
            "retrieval_passed": False,
            "retrieval_failure_reason": "document_not_found",
            "generation_passed": False,
            "generation_failure_reason": "not_evaluated",
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


def format_bool(value: bool) -> str:
    return "是" if value else "否"


def build_document_ingestion_agent_report(result: dict) -> str:
    lines = [
        "# PostgreSQL 文档入库 Agent 验收报告",
        "",
        "## 验收结论",
        "",
        f"- 是否通过：{format_bool(result['passed'])}",
        f"- 失败原因：{result['failure_reason']}",
        f"- 检索层是否通过：{format_bool(result['retrieval_passed'])}",
        f"- 检索层失败原因：{result['retrieval_failure_reason']}",
        f"- 生成层是否通过：{format_bool(result['generation_passed'])}",
        f"- 生成层失败原因：{result['generation_failure_reason']}",
        "",
        "## 验收对象",
        "",
        f"- 文档标题：{result['title']}",
        f"- 问题：{result['question']}",
        f"- 检索后端：{result['retriever_backend']}",
        f"- 检索模式：{result['mode']}",
        f"- top_k：{result['top_k']}",
        f"- min_score：{result['min_score']}",
        "",
        "## Agent 状态",
        "",
        f"- has_valid_context：{format_bool(result['has_valid_context'])}",
        f"- 是否兜底回答：{format_bool(result['is_fallback'])}",
        f"- 是否引用目标文档：{format_bool(result['cited_expected_document'])}",
        f"- Top1 是否引用目标文档：{format_bool(result['top_citation_matched'])}",
        f"- 引用数量：{result['citation_count']}",
        "",
        "## 回答",
        "",
        result["answer"] if result["answer"] != "" else "（空）",
        "",
        "## 引用来源",
        "",
    ]

    if result["citations"] == []:
        lines.append("无引用。")
    else:
        for index, citation in enumerate(result["citations"], start=1):
            lines.append(
                f"- [{index}] {citation.get('title', '')} - {citation.get('path', '')}"
            )
            if citation.get("text", "") != "":
                lines.append(f"  - 片段：{citation['text']}")

    lines.extend(
        [
            "",
            "## 检索片段",
            "",
        ]
    )

    snippets = result.get("snippets", [])

    if snippets == []:
        lines.append("无片段。")
    else:
        for index, snippet in enumerate(snippets, start=1):
            lines.append(
                f"- [{index}] {snippet.get('title', '')} - {snippet.get('path', '')}"
            )
            if snippet.get("score") is not None:
                lines.append(f"  - 分数：{snippet['score']}")
            if snippet.get("text", "") != "":
                lines.append(f"  - 片段：{snippet['text']}")

    lines.append("")

    return "\n".join(lines)


def write_document_ingestion_agent_report(
    result: dict,
    report_path: str | Path = DEFAULT_DOCUMENT_INGESTION_AGENT_REPORT_PATH,
) -> Path:
    path = Path(report_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_document_ingestion_agent_report(result), encoding="utf-8")
    return path


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate whether an ingested PostgreSQL document can answer through the Agent.",
    )
    parser.add_argument("--title", required=True)
    parser.add_argument("--question", required=True)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--min-score", type=float, default=0.6)
    parser.add_argument("--timeout-seconds", type=float, default=30)
    parser.add_argument(
        "--report-path",
        default="",
        help=(
            "Optional Markdown report path. Example: "
            f"{DEFAULT_DOCUMENT_INGESTION_AGENT_REPORT_PATH}"
        ),
    )
    return parser


def print_evaluation_result(result: dict) -> None:
    print("PostgreSQL 文档入库 Agent 验收完成。")
    print("是否通过：", result["passed"])
    print("失败原因：", result["failure_reason"])
    print("检索层是否通过：", result["retrieval_passed"])
    print("检索层失败原因：", result["retrieval_failure_reason"])
    print("生成层是否通过：", result["generation_passed"])
    print("生成层失败原因：", result["generation_failure_reason"])
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
        raise SystemExit(1)

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

    if args.report_path != "":
        report_path = write_document_ingestion_agent_report(result, args.report_path)
        print("验收报告已保存：", report_path)

    if result["passed"] is not True:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
