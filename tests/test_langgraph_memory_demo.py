from week09.langgraph_memory_demo import build_memory_graph, run_memory_graph


def test_memory_graph_remembers_name_in_same_thread():
    graph = build_memory_graph()

    first_result = run_memory_graph("我叫陈晨", "thread-1", graph)
    second_result = run_memory_graph("我叫什么？", "thread-1", graph)

    assert first_result["remembered_name"] == "陈晨"
    assert "我记住了" in first_result["answer"]

    assert second_result["remembered_name"] == "陈晨"
    assert second_result["answer"] == "你叫陈晨。"
    assert second_result["messages"] == ["我叫陈晨", "我叫什么？"]


def test_memory_graph_does_not_share_memory_between_threads():
    graph = build_memory_graph()

    run_memory_graph("我叫陈晨", "thread-1", graph)
    result = run_memory_graph("我叫什么？", "thread-2", graph)

    assert result["remembered_name"] is None
    assert result["answer"] == "我还不知道你的名字。"
    assert result["messages"] == ["我叫什么？"]


def test_memory_graph_records_steps():
    graph = build_memory_graph()

    result = run_memory_graph("我叫陈晨", "thread-1", graph)

    assert result["steps"] == ["remember_name: 我叫陈晨"]