from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph


class MinimalAgentState(TypedDict):
    question: str
    intent: str | None
    answer: str | None
    steps: list[str]


def decide_intent_node(state: MinimalAgentState) -> dict:
    question = state["question"]

    if "哪些文档" in question or "列出" in question:
        intent = "list_documents"
    elif "查看" in question or "读取" in question:
        intent = "read_document"
    else:
        intent = "answer_question"

    return {
        "intent": intent,
        "steps": state["steps"] + [f"判断意图：{intent}"],
    }


def route_by_intent(
    state: MinimalAgentState,
) -> Literal["list_documents_node", "read_document_node", "answer_question_node"]:
    if state["intent"] == "list_documents":
        return "list_documents_node"

    if state["intent"] == "read_document":
        return "read_document_node"

    return "answer_question_node"


def list_documents_node(state: MinimalAgentState) -> dict:
    return {
        "answer": "当前知识库有：员工手册、请假制度、远程办公制度",
        "steps": state["steps"] + ["列出文档"],
    }


def read_document_node(state: MinimalAgentState) -> dict:
    return {
        "answer": "这里是某份文档的内容片段",
        "steps": state["steps"] + ["读取文档"],
    }


def answer_question_node(state: MinimalAgentState) -> dict:
    return {
        "answer": "这是根据知识库生成的回答",
        "steps": state["steps"] + ["知识库问答"],
    }


def build_graph():
    graph_builder = StateGraph(MinimalAgentState)

    graph_builder.add_node("decide_intent_node", decide_intent_node)
    graph_builder.add_node("list_documents_node", list_documents_node)
    graph_builder.add_node("read_document_node", read_document_node)
    graph_builder.add_node("answer_question_node", answer_question_node)

    graph_builder.add_edge(START, "decide_intent_node")

    graph_builder.add_conditional_edges(
        "decide_intent_node",
        route_by_intent,
        [
            "list_documents_node",
            "read_document_node",
            "answer_question_node",
        ],
    )

    graph_builder.add_edge("list_documents_node", END)
    graph_builder.add_edge("read_document_node", END)
    graph_builder.add_edge("answer_question_node", END)

    return graph_builder.compile()


def run_langgraph(question: str) -> MinimalAgentState:
    graph = build_graph()

    initial_state: MinimalAgentState = {
        "question": question,
        "intent": None,
        "answer": None,
        "steps": [],
    }

    return graph.invoke(initial_state)