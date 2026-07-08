from week09.pseudo_langgraph_agent import run_graph


def test_run_graph_lists_documents():
    state = run_graph("知识库有哪些文档？")

    assert state["intent"] == "list_documents"
    assert "员工手册" in state["answer"]
    assert "判断意图：list_documents" in state["steps"]
    assert "列出文档" in state["steps"]


def test_run_graph_reads_document():
    state = run_graph("查看员工手册")

    assert state["intent"] == "read_document"
    assert "文档的内容片段" in state["answer"]
    assert "判断意图：read_document" in state["steps"]
    assert "读取文档" in state["steps"]


def test_run_graph_answers_question():
    state = run_graph("员工可以远程办公吗？")

    assert state["intent"] == "answer_question"
    assert state["has_context"] is True
    assert "根据知识库生成的回答" in state["answer"]
    assert "判断意图：answer_question" in state["steps"]
    assert "知识库问答" in state["steps"]


def test_run_graph_refuses_when_no_context():
    state = run_graph("公司有没有股票期权？")

    assert state["intent"] == "answer_question"
    assert state["has_context"] is False
    assert "未找到知识库证据" in state["steps"]
    assert state["answer"] == "知识库中没有找到相关资料，暂时无法回答。"