from typing import Callable, Literal, TypedDict

from langgraph.graph import END, START, StateGraph

from backend.services.agent_tools import (
    answer_with_context_tool,
    ask_clarification_tool,
    find_document_by_title_tool,
    list_documents_tool,
    read_document_chunks_tool,
    refuse_answer_tool,
    search_knowledge_base_tool,
)
from backend.services.conversation_context_service import (
    build_contextual_question,
    find_latest_cited_document_title,
    infer_document_title_from_messages,
)
from backend.services.simple_agent import decide_agent_intent, extract_document_title
from week04.settings import SQLITE_DATABASE_PATH


class LangGraphAgentState(TypedDict):
    question: str
    messages: list[dict]
    intent: str | None
    keyword: str
    contextual_question: str
    context_document_title: str
    snippets: list[dict]
    has_valid_context: bool
    document_title: str
    document: dict | None
    document_match_type: str | None
    missing_field: str
    answer: str | None
    citations: list[dict]
    steps: list[dict]
    database_path: str
    top_k: int
    mode: str
    min_score: float
    generator: Callable[[str], str]


def decide_intent_node(state: LangGraphAgentState) -> dict:
    intent = decide_agent_intent(state["question"])

    return {
        "intent": intent,
        "steps": state["steps"]
        + [
            {
                "step": len(state["steps"]) + 1,
                "tool": "decide_agent_intent",
                "input": {"question": state["question"]},
                "observation": {"intent": intent},
                "next_action": "route_by_intent",
            }
        ],
    }


def route_by_intent(
    state: LangGraphAgentState,
) -> Literal[
    "list_documents_node",
    "extract_document_title_node",
    "search_knowledge_node",
]:
    if state["intent"] == "list_documents":
        return "list_documents_node"

    if state["intent"] == "read_document":
        return "extract_document_title_node"

    return "search_knowledge_node"


def list_documents_node(state: LangGraphAgentState) -> dict:
    tool_result = list_documents_tool(state["database_path"])

    document_titles = []

    for document in tool_result["documents"]:
        document_titles.append(document["title"])

    answer = "当前知识库文档：\n"

    for title in document_titles:
        answer = answer + f"- {title}\n"

    return {
        "keyword": "文档列表",
        "answer": answer.strip(),
        "citations": [],
        "steps": state["steps"]
        + [
            {
                "step": len(state["steps"]) + 1,
                "tool": "list_documents_tool",
                "input": {},
                "observation": {
                    "document_count": tool_result["count"],
                },
                "next_action": "finish",
            }
        ],
    }


def extract_document_title_node(state: LangGraphAgentState) -> dict:
    document_title = extract_document_title(state["question"])
    source = "question"

    if document_title == "":
        document_title = infer_document_title_from_messages(state["messages"])
        source = "messages"

    if document_title == "":
        missing_field = "文档标题"
        next_action = "ask_clarification_node"
        source = "none"
    else:
        missing_field = ""
        next_action = "find_document_node"

    return {
        "keyword": document_title if document_title != "" else "文档标题",
        "document_title": document_title,
        "missing_field": missing_field,
        "steps": state["steps"]
        + [
            {
                "step": len(state["steps"]) + 1,
                "tool": "extract_document_title",
                "input": {
                    "question": state["question"],
                },
                "observation": {
                    "document_title": document_title,
                    "missing_field": missing_field,
                    "source": source,
                },
                "next_action": next_action,
            }
        ],
    }


def route_by_document_title(
    state: LangGraphAgentState,
) -> Literal["find_document_node", "ask_clarification_node"]:
    if state["document_title"] == "":
        return "ask_clarification_node"

    return "find_document_node"


def find_document_node(state: LangGraphAgentState) -> dict:
    document_result = find_document_by_title_tool(
        title=state["document_title"],
        database_path=state["database_path"],
    )

    found = document_result["found"]

    if found:
        next_action = "read_document_chunks_node"
        missing_field = ""
    else:
        next_action = "ask_correct_title_node"
        missing_field = "正确的文档标题"

    return {
        "document": document_result["document"],
        "document_match_type": document_result["match_type"],
        "missing_field": missing_field,
        "steps": state["steps"]
        + [
            {
                "step": len(state["steps"]) + 1,
                "tool": "find_document_by_title_tool",
                "input": {
                    "title": state["document_title"],
                },
                "observation": {
                    "found": found,
                    "document_id": (
                        document_result["document"]["id"] if found else None
                    ),
                    "match_type": document_result["match_type"],
                },
                "next_action": next_action,
            }
        ],
    }


def route_by_document_found(
    state: LangGraphAgentState,
) -> Literal["read_document_chunks_node", "ask_correct_title_node"]:
    if state["document"] is None:
        return "ask_correct_title_node"

    return "read_document_chunks_node"


def ask_clarification_node(state: LangGraphAgentState) -> dict:
    tool_result = ask_clarification_tool(
        question=state["question"],
        missing_field=state["missing_field"],
    )

    return {
        "answer": tool_result["answer"],
        "citations": [],
        "steps": state["steps"]
        + [
            {
                "step": len(state["steps"]) + 1,
                "tool": "ask_clarification_tool",
                "input": {
                    "missing_field": state["missing_field"],
                },
                "observation": {
                    "answer": tool_result["answer"],
                },
                "next_action": "finish",
            }
        ],
    }


def ask_correct_title_node(state: LangGraphAgentState) -> dict:
    tool_result = ask_clarification_tool(
        question=state["question"],
        missing_field=state["missing_field"],
    )

    return {
        "answer": tool_result["answer"],
        "citations": [],
        "steps": state["steps"]
        + [
            {
                "step": len(state["steps"]) + 1,
                "tool": "ask_clarification_tool",
                "input": {
                    "missing_field": state["missing_field"],
                },
                "observation": {
                    "answer": tool_result["answer"],
                },
                "next_action": "finish",
            }
        ],
    }


def read_document_chunks_node(state: LangGraphAgentState) -> dict:
    document = state["document"]

    chunks_result = read_document_chunks_tool(
        document_id=document["id"],
        database_path=state["database_path"],
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
        "answer": answer,
        "citations": citations,
        "steps": state["steps"]
        + [
            {
                "step": len(state["steps"]) + 1,
                "tool": "read_document_chunks_tool",
                "input": {
                    "document_id": document["id"],
                },
                "observation": {
                    "chunk_count": len(chunks),
                },
                "next_action": "finish",
            }
        ],
    }


def search_knowledge_node(state: LangGraphAgentState) -> dict:
    context_document_title = find_latest_cited_document_title(state["messages"])

    contextual_question = build_contextual_question(
        question=state["question"],
        messages=state["messages"],
    )

    tool_result = search_knowledge_base_tool(
        question=contextual_question,
        database_path=state["database_path"],
        top_k=state["top_k"],
        mode=state["mode"],
        min_score=state["min_score"],
    )

    snippets = tool_result["snippets"]

    next_action = "validate_context"

    return {
        "keyword": tool_result["keyword"],
        "contextual_question": contextual_question,
        "context_document_title": context_document_title,
        "snippets": snippets,
        "steps": state["steps"]
        + [
            {
                "step": len(state["steps"]) + 1,
                "tool": "search_knowledge_base_tool",
                "input": {
                    "question": state["question"],
                    "contextual_question": contextual_question,
                    "context_document_title": context_document_title,
                    "top_k": state["top_k"],
                    "mode": state["mode"],
                    "min_score": state["min_score"],
                },
                "observation": {
                    "keyword": tool_result["keyword"],
                    "result_count": tool_result["count"],
                },
                "next_action": next_action,
            }
        ],
    }


def is_context_valid(keyword: str, snippets: list[dict]) -> bool:
    if snippets == []:
        return False

    if keyword == "":
        return True

    for snippet in snippets:
        if keyword in snippet["text"]:
            return True

    return False


def is_contextual_context_valid(
    context_document_title: str,
    snippets: list[dict],
) -> bool:
    if context_document_title == "":
        return False

    for snippet in snippets:
        if snippet["title"] != context_document_title:
            continue

        if "score" not in snippet:
            return True

        if snippet["score"] > 0:
            return True

    return False


def validate_context_node(state: LangGraphAgentState) -> dict:
    has_valid_context = is_context_valid(
        keyword=state["keyword"],
        snippets=state["snippets"],
    )

    if not has_valid_context:
        has_valid_context = is_contextual_context_valid(
            context_document_title=state["context_document_title"],
            snippets=state["snippets"],
        )

    if has_valid_context:
        next_action = "answer_node"
    else:
        next_action = "refuse_node"

    return {
        "has_valid_context": has_valid_context,
        "steps": state["steps"]
        + [
            {
                "step": len(state["steps"]) + 1,
                "tool": "validate_context_node",
                "input": {
                    "keyword": state["keyword"],
                    "snippet_count": len(state["snippets"]),
                },
                "observation": {
                    "has_valid_context": has_valid_context,
                },
                "next_action": next_action,
            }
        ],
    }


def route_by_context(
    state: LangGraphAgentState,
) -> Literal["answer_node", "refuse_node"]:
    if state["has_valid_context"]:
        return "answer_node"

    return "refuse_node"


def answer_node(state: LangGraphAgentState) -> dict:
    tool_result = answer_with_context_tool(
        question=state["question"],
        snippets=state["snippets"],
        generator=state["generator"],
    )

    return {
        "answer": tool_result["answer"],
        "citations": tool_result["citations"],
        "steps": state["steps"]
        + [
            {
                "step": len(state["steps"]) + 1,
                "tool": "answer_with_context_tool",
                "input": {
                    "question": state["question"],
                    "snippet_count": len(state["snippets"]),
                },
                "observation": {
                    "citation_count": len(tool_result["citations"]),
                },
                "next_action": "finish",
            }
        ],
    }


def refuse_node(state: LangGraphAgentState) -> dict:
    tool_result = refuse_answer_tool(state["question"])

    return {
        "answer": tool_result["answer"],
        "citations": tool_result["citations"],
        "steps": state["steps"]
        + [
            {
                "step": len(state["steps"]) + 1,
                "tool": "refuse_answer_tool",
                "input": {
                    "question": state["question"],
                    "snippet_count": len(state["snippets"]),
                },
                "observation": {
                    "citation_count": 0,
                },
                "next_action": "finish",
            }
        ],
    }


def build_langgraph_agent():
    graph_builder = StateGraph(LangGraphAgentState)

    graph_builder.add_node("decide_intent_node", decide_intent_node)
    graph_builder.add_node("list_documents_node", list_documents_node)
    graph_builder.add_node("search_knowledge_node", search_knowledge_node)
    graph_builder.add_node("validate_context_node", validate_context_node)
    graph_builder.add_node("answer_node", answer_node)
    graph_builder.add_node("refuse_node", refuse_node)
    graph_builder.add_node("extract_document_title_node", extract_document_title_node)
    graph_builder.add_node("find_document_node", find_document_node)
    graph_builder.add_node("ask_clarification_node", ask_clarification_node)
    graph_builder.add_node("ask_correct_title_node", ask_correct_title_node)
    graph_builder.add_node("read_document_chunks_node", read_document_chunks_node)

    graph_builder.add_edge(START, "decide_intent_node")

    graph_builder.add_conditional_edges(
        "decide_intent_node",
        route_by_intent,
        [
            "list_documents_node",
            "extract_document_title_node",
            "search_knowledge_node",
        ],
    )

    graph_builder.add_edge("list_documents_node", END)

    graph_builder.add_conditional_edges(
        "extract_document_title_node",
        route_by_document_title,
        [
            "find_document_node",
            "ask_clarification_node",
        ],
    )

    graph_builder.add_conditional_edges(
        "find_document_node",
        route_by_document_found,
        [
            "read_document_chunks_node",
            "ask_correct_title_node",
        ],
    )

    graph_builder.add_edge("ask_clarification_node", END)
    graph_builder.add_edge("ask_correct_title_node", END)
    graph_builder.add_edge("read_document_chunks_node", END)

    graph_builder.add_edge("search_knowledge_node", "validate_context_node")

    graph_builder.add_conditional_edges(
        "validate_context_node",
        route_by_context,
        [
            "answer_node",
            "refuse_node",
        ],
    )

    graph_builder.add_edge("answer_node", END)
    graph_builder.add_edge("refuse_node", END)

    return graph_builder.compile()


def run_langgraph_agent(
    question: str,
    database_path: str = SQLITE_DATABASE_PATH,
    top_k: int = 3,
    mode: str = "keyword",
    min_score: float = 0.0,
    generator: Callable[[str], str] = lambda prompt: "这是模型回答",
    messages: list[dict] | None = None,
) -> LangGraphAgentState:
    graph = build_langgraph_agent()

    initial_state: LangGraphAgentState = {
        "question": question,
        "messages": messages if messages is not None else [],
        "intent": None,
        "keyword": "",
        "contextual_question": question,
        "context_document_title": "",
        "snippets": [],
        "has_valid_context": False,
        "document_title": "",
        "document": None,
        "document_match_type": None,
        "missing_field": "",
        "answer": None,
        "citations": [],
        "steps": [],
        "database_path": database_path,
        "top_k": top_k,
        "mode": mode,
        "min_score": min_score,
        "generator": generator,
    }

    return graph.invoke(initial_state)