from typing import Callable, Literal, TypedDict

from langgraph.graph import END, START, StateGraph

from backend.services.agent_tools import (
    answer_with_context_tool,
    list_documents_tool,
    refuse_answer_tool,
    search_knowledge_base_tool,
)
from backend.services.simple_agent import decide_agent_intent
from week04.settings import SQLITE_DATABASE_PATH


class LangGraphAgentState(TypedDict):
    question: str
    intent: str | None
    keyword: str
    snippets: list[dict]
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
) -> Literal["list_documents_node", "search_knowledge_node"]:
    if state["intent"] == "list_documents":
        return "list_documents_node"

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


def search_knowledge_node(state: LangGraphAgentState) -> dict:
    tool_result = search_knowledge_base_tool(
        question=state["question"],
        database_path=state["database_path"],
        top_k=state["top_k"],
        mode=state["mode"],
        min_score=state["min_score"],
    )

    snippets = tool_result["snippets"]

    if snippets:
        next_action = "answer_node"
    else:
        next_action = "refuse_node"

    return {
        "keyword": tool_result["keyword"],
        "snippets": snippets,
        "steps": state["steps"]
        + [
            {
                "step": len(state["steps"]) + 1,
                "tool": "search_knowledge_base_tool",
                "input": {
                    "question": state["question"],
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


def route_by_context(
    state: LangGraphAgentState,
) -> Literal["answer_node", "refuse_node"]:
    if state["snippets"]:
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
    graph_builder.add_node("answer_node", answer_node)
    graph_builder.add_node("refuse_node", refuse_node)

    graph_builder.add_edge(START, "decide_intent_node")

    graph_builder.add_conditional_edges(
        "decide_intent_node",
        route_by_intent,
        [
            "list_documents_node",
            "search_knowledge_node",
        ],
    )

    graph_builder.add_edge("list_documents_node", END)

    graph_builder.add_conditional_edges(
        "search_knowledge_node",
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
) -> LangGraphAgentState:
    graph = build_langgraph_agent()

    initial_state: LangGraphAgentState = {
        "question": question,
        "intent": None,
        "keyword": "",
        "snippets": [],
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