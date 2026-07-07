"""A minimal Agent workflow built from tool functions."""

from typing import Callable

from backend.config import DEFAULT_MIN_SCORE, DEFAULT_TOP_K
from backend.services.agent_tools import (
    answer_with_context_tool,
    ask_clarification_tool,
    find_document_by_title_tool,
    list_documents_tool,
    read_document_chunks_tool,
    refuse_answer_tool,
    search_knowledge_base_tool,
)
from backend.services.ollama_service import generate_with_ollama
from week04.settings import SQLITE_DATABASE_PATH


def decide_agent_intent(question: str) -> str:
    """判断用户问题应该使用哪类 Agent 能力。"""
    if "有哪些文档" in question:
        return "list_documents"

    if "列出文档" in question:
        return "list_documents"

    if "文档列表" in question:
        return "list_documents"

    if "查看" in question and ("片段" in question or "内容" in question):
        return "read_document"

    if "读取" in question and ("片段" in question or "内容" in question):
        return "read_document"

    if "有哪些内容" in question:
        return "read_document"

    return "answer_question"


def extract_document_title(question: str) -> str:
    """从用户问题中提取文档标题。"""
    title = question.strip()

    for prefix in ["请帮我查看", "帮我查看", "请查看", "查看", "请读取", "读取"]:
        if title.startswith(prefix):
            title = title.removeprefix(prefix)

    for suffix in ["有哪些内容？", "有哪些内容", "的片段", "的内容", "片段", "内容", "？", "?"]:
        title = title.replace(suffix, "")

    title = title.strip()

    if title in ["这份文档", "这个文档", "文档", "这份", "这个"]:
        return ""

    return title


def run_simple_agent(
    question: str,
    database_path: str = SQLITE_DATABASE_PATH,
    top_k: int = DEFAULT_TOP_K,
    mode: str = "keyword",
    min_score: float = DEFAULT_MIN_SCORE,
    generator: Callable[[str], str] = generate_with_ollama,
) -> dict:
    intent = decide_agent_intent(question)

    if intent == "list_documents":
        tool_result = list_documents_tool(database_path)

        document_titles = []

        for document in tool_result["documents"]:
            document_titles.append(document["title"])

        if document_titles == []:
            answer = "知识库中还没有文档。"
        else:
            answer = "知识库中有这些文档：" + "、".join(document_titles)

        return {
            "question": question,
            "keyword": "文档列表",
            "answer": answer,
            "citations": [],
            "steps": [
                {
                    "step": 1,
                    "tool": "decide_agent_intent",
                    "input": {
                        "question": question,
                    },
                    "observation": {
                        "intent": intent,
                    },
                    "next_action": "list_documents",
                },
                {
                    "step": 2,
                    "tool": "list_documents_tool",
                    "input": {},
                    "observation": {
                        "document_count": tool_result["count"],
                        "document_titles": document_titles,
                    },
                    "next_action": "finish",
                },
            ],
        }

    if intent == "read_document":
        document_title = extract_document_title(question)

        if document_title == "":
            final_result = ask_clarification_tool(question, "文档标题")

            return {
                "question": question,
                "keyword": "文档标题",
                "answer": final_result["answer"],
                "citations": [],
                "steps": [
                    {
                        "step": 1,
                        "tool": "decide_agent_intent",
                        "input": {
                            "question": question,
                        },
                        "observation": {
                            "intent": intent,
                        },
                        "next_action": "extract_document_title",
                    },
                    {
                        "step": 2,
                        "tool": "extract_document_title",
                        "input": {
                            "question": question,
                        },
                        "observation": {
                            "document_title": "",
                            "missing_field": "文档标题",
                        },
                        "next_action": "ask_clarification",
                    },
                    {
                        "step": 3,
                        "tool": "ask_clarification_tool",
                        "input": {
                            "missing_field": "文档标题",
                        },
                        "observation": {
                            "answer": final_result["answer"],
                        },
                        "next_action": "finish",
                    },
                ],
            }

        document_result = find_document_by_title_tool(
            title=document_title,
            database_path=database_path,
        )

        if document_result["found"] == False:
            final_result = ask_clarification_tool(question, "正确的文档标题")

            return {
                "question": question,
                "keyword": document_title,
                "answer": final_result["answer"],
                "citations": [],
                "steps": [
                    {
                        "step": 1,
                        "tool": "decide_agent_intent",
                        "input": {
                            "question": question,
                        },
                        "observation": {
                            "intent": intent,
                        },
                        "next_action": "extract_document_title",
                    },
                    {
                        "step": 2,
                        "tool": "extract_document_title",
                        "input": {
                            "question": question,
                        },
                        "observation": {
                            "document_title": document_title,
                        },
                        "next_action": "find_document_by_title",
                    },
                    {
                        "step": 3,
                        "tool": "find_document_by_title_tool",
                        "input": {
                            "title": document_title,
                        },
                        "observation": {
                            "found": False,
                            "match_type": document_result["match_type"],
                        },
                        "next_action": "ask_clarification",
                    },
                    {
                        "step": 4,
                        "tool": "ask_clarification_tool",
                        "input": {
                            "missing_field": "正确的文档标题",
                        },
                        "observation": {
                            "answer": final_result["answer"],
                        },
                        "next_action": "finish",
                    },
                ],
            }

        document = document_result["document"]

        chunks_result = read_document_chunks_tool(
            document_id=document["id"],
            database_path=database_path,
        )

        chunks = chunks_result["chunks"]

        chunk_lines = []

        for index, chunk in enumerate(chunks, start=1):
            chunk_lines.append(f"[{index}] {chunk['text']}")

        answer = document["title"] + " 的片段如下：\n" + "\n".join(chunk_lines)

        citations = []

        for chunk in chunks:
            citations.append(
                {
                    "title": document["title"],
                    "text": chunk["text"],
                    "path": "sqlite://" + str(document["id"]),
                }
            )

        return {
            "question": question,
            "keyword": document_title,
            "answer": answer,
            "citations": citations,
            "steps": [
                {
                    "step": 1,
                    "tool": "decide_agent_intent",
                    "input": {
                        "question": question,
                    },
                    "observation": {
                        "intent": intent,
                    },
                    "next_action": "extract_document_title",
                },
                {
                    "step": 2,
                    "tool": "extract_document_title",
                    "input": {
                        "question": question,
                    },
                    "observation": {
                        "document_title": document_title,
                    },
                    "next_action": "find_document_by_title",
                },
                {
                    "step": 3,
                    "tool": "find_document_by_title_tool",
                    "input": {
                        "title": document_title,
                    },
                    "observation": {
                        "found": True,
                        "document_id": document["id"],
                        "match_type": document_result["match_type"],
                    },
                    "next_action": "read_document_chunks",
                },
                {
                    "step": 4,
                    "tool": "read_document_chunks_tool",
                    "input": {
                        "document_id": document["id"],
                    },
                    "observation": {
                        "chunk_count": len(chunks),
                    },
                    "next_action": "finish",
                },
            ],
        }

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
                "tool": "decide_agent_intent",
                "input": {
                    "question": question,
                },
                "observation": {
                    "intent": intent,
                },
                "next_action": "search_knowledge_base",
            },
            {
                "step": 2,
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
                "step": 3,
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