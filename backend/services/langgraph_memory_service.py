from week09.langgraph_memory_demo import build_memory_graph, run_memory_graph


memory_graph = build_memory_graph()


def chat_with_memory(
    message: str,
    thread_id: str,
) -> dict:
    return run_memory_graph(
        message=message,
        thread_id=thread_id,
        graph=memory_graph,
    )