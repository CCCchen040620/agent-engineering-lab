from week09.langgraph_minimal_agent import run_langgraph


def test_langgraph_lists_documents():
    state = run_langgraph("知识库有哪些文档？")

    assert state["intent"] == "list_documents"
    assert "员工手册" in state["answer"]
    assert "判断意图：list_documents" in state["steps"]
    assert "列出文档" in state["steps"]


def test_langgraph_reads_document():
    state = run_langgraph("查看员工手册")

    assert state["intent"] == "read_document"
    assert "文档的内容片段" in state["answer"]
    assert "判断意图：read_document" in state["steps"]
    assert "读取文档" in state["steps"]


def test_langgraph_answers_question():
    state = run_langgraph("员工可以远程办公吗？")

    assert state["intent"] == "answer_question"
    assert "根据知识库生成的回答" in state["answer"]
    assert "判断意图：answer_question" in state["steps"]
    assert "知识库问答" in state["steps"]