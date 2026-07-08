from operator import add
from typing import Annotated, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph


class MemoryDemoState(TypedDict):
    messages: Annotated[list[str], add]
    remembered_name: str | None
    answer: str
    steps: Annotated[list[str], add]


def memory_node(state: MemoryDemoState) -> dict:
    latest_message = state["messages"][-1]
    remembered_name = state.get("remembered_name")

    if "我叫什么" in latest_message:
        if remembered_name is None:
            answer = "我还不知道你的名字。"
            action = "missing_memory"
        else:
            answer = f"你叫{remembered_name}。"
            action = "recall_name"
    elif "我叫" in latest_message:
        remembered_name = latest_message.split("我叫", 1)[1].strip()
        answer = f"我记住了，你叫{remembered_name}。"
        action = "remember_name"
    else:
        answer = "我会根据当前对话继续回答。"
        action = "general_reply"

    return {
        "remembered_name": remembered_name,
        "answer": answer,
        "steps": [f"{action}: {latest_message}"],
    }


def build_memory_graph():
    graph_builder = StateGraph(MemoryDemoState)

    graph_builder.add_node("memory_node", memory_node)

    graph_builder.add_edge(START, "memory_node")
    graph_builder.add_edge("memory_node", END)

    checkpointer = InMemorySaver()

    return graph_builder.compile(checkpointer=checkpointer)


def run_memory_graph(
    message: str,
    thread_id: str,
    graph=None,
) -> MemoryDemoState:
    if graph is None:
        graph = build_memory_graph()

    initial_state = {
        "messages": [message],
        "steps": [],
    }

    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    return graph.invoke(initial_state, config)