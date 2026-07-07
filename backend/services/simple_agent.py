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
        final_result = refuse_answer_tool(question)
    else:
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
                "name": "search_knowledge_base",
                "status": "completed",
                "result_count": search_result["count"],
            },
            {
                "name": "answer_or_refuse",
                "status": "completed",
                "action": "refuse"
                if search_result["snippets"] == []
                else "answer_with_context",
            },
        ],
    }