from typing import TypedDict


class AgentState(TypedDict):
    question: str
    intent: str | None
    answer: str | None
    steps: list[str]


def create_initial_state(question: str) -> AgentState:
    return {
        "question": question,
        "intent": None,
        "answer": None,
        "steps": [],
    }


def decide_intent_node(state: AgentState) -> AgentState:
    question = state["question"]

    if "哪些文档" in question or "列出" in question:
        state["intent"] = "list_documents"
    elif "查看" in question or "读取" in question:
        state["intent"] = "read_document"
    else:
        state["intent"] = "answer_question"

    state["steps"].append(f"判断意图：{state['intent']}")

    return state


def route_by_intent(state: AgentState) -> str:
    intent = state["intent"]

    if intent == "list_documents":
        return "list_documents_node"

    if intent == "read_document":
        return "read_document_node"

    return "answer_question_node"


def list_documents_node(state: AgentState) -> AgentState:
    state["steps"].append("列出文档")
    state["answer"] = "当前知识库有：员工手册、请假制度、远程办公制度"
    return state


def read_document_node(state: AgentState) -> AgentState:
    state["steps"].append("读取文档")
    state["answer"] = "这里是某份文档的内容片段"
    return state


def answer_question_node(state: AgentState) -> AgentState:
    state["steps"].append("知识库问答")
    state["answer"] = "这是根据知识库生成的回答"
    return state


def run_graph(question: str) -> AgentState:
    state = create_initial_state(question)

    state = decide_intent_node(state)

    next_node = route_by_intent(state)

    if next_node == "list_documents_node":
        state = list_documents_node(state)
    elif next_node == "read_document_node":
        state = read_document_node(state)
    else:
        state = answer_question_node(state)

    return state