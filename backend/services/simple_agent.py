"""A minimal Agent workflow built from tool functions."""

from typing import Callable

from backend.config import DEFAULT_MIN_SCORE, DEFAULT_TOP_K
from backend.services.agent_tools import (
    answer_with_context_tool,
    refuse_answer_tool,
    search_knowledge_base_tool,
)
from backend.services.ollama_service import generate_with_ollama
from week04.settings import SQLITE_DATABASE_PATH


def run_simple_agent(
    question: str,
    database_path: str = SQLITE_DATABASE_PATH,
    top_k: int = DEFAULT_TOP_K,
    mode: str = "keyword",
    min_score: float = DEFAULT_MIN_SCORE,
    generator: Callable[[str], str] = generate_with_ollama,
) -> dict:
    """运行一个最小版知识库 Agent。"""
    search_result = search_knowledge_base_tool(
        question=question,
        database_path=database_path,
        top_k=top_k,
        mode=mode,
        min_score=min_score,
    )

    if search_result["snippets"] == []:
        next_action = "refuse"
        final_result = refuse_answer_tool(question)
    else:
        next_action = "answer_with_context"
        final_result = answer_with_context_tool(
            question=question,
            snippets=search_result["snippets"],
            generator=generator,
        )

    return {
        "question": question,
        "keyword": search_result["keyword"],
        "answer": final_result["answer"],
        "citations": final_result["citations"],
        "steps": [
            {
                "step": 1,
                "tool": "search_knowledge_base_tool",
                "input": {
                    "question": question,
                    "mode": mode,
                    "top_k": top_k,
                    "min_score": min_score,
                },
                "observation": {
                    "keyword": search_result["keyword"],
                    "result_count": search_result["count"],
                },
                "next_action": next_action,
            },
            {
                "step": 2,
                "tool": "refuse_answer_tool"
                if next_action == "refuse"
                else "answer_with_context_tool",
                "input": {
                    "snippet_count": search_result["count"],
                },
                "observation": {
                    "citation_count": len(final_result["citations"]),
                },
                "next_action": "finish",
            },
        ],
    }