# 最小 LangGraph Agent 学习笔记

## 1. 本节目标

这一节我完成了什么？

- 用 LangGraph 写了第一个最小 Agent。
- 学会了 `StateGraph`、`add_node`、`add_edge`、`add_conditional_edges`、`compile`、`invoke`。
- 对比了伪 Graph 和真实 LangGraph 的区别。

## 2. 当前文件

本节相关文件：

```text
week09/langgraph_minimal_agent.py
tests/test_langgraph_minimal_agent.py
week09/pseudo_langgraph_agent.py

langgraph_minimal_agent.py 是真正使用 LangGraph 的版本。
test_langgraph_minimal_agent.py 是自动化测试。
pseudo_langgraph_agent.py 是之前手写模拟版本，用来对照理解。

StateGraph 是 LangGraph 用来创建图的工具。
MinimalAgentState 规定了图运行时 State 的结构。
这一步不是运行 Agent，而是在准备搭建 Graph。
StateGraph 像画流程图的画布，MinimalAgentState 像流程图中流动的数据格式。

add_node 是把 Python 函数注册成图里的节点。
第一个参数是节点名字。
第二个参数是真正执行的函数。
节点负责接收 State，并返回要更新的字段。

START 表示图的起点。
END 表示图的终点。
add_edge 表示固定路线。
例如从 START 固定进入 decide_intent_node

add_conditional_edges表示条件分流。
decide_intent_node 执行完后，不是固定去一个节点。
LangGraph 会调用 route_by_intent。
route_by_intent 返回哪个节点名，流程就走向哪个节点。
这替代了之前伪 Graph 里的手写 if/elif/else。

compile 是把前面注册好的节点和边编译成一个可以运行的 Graph。
在 compile 之前，它更像“图的配置”。
在 compile 之后，才可以调用 invoke 运行。

invoke 是真正执行 Graph。
它接收初始 State。
然后按照节点和边自动运行。
最后返回最终 State。
伪 Graph：run_graph(question)
LangGraph：graph.invoke(initial_state)

| 对比项 | 伪 Graph | LangGraph |
|---|---|---|
| State | 自己定义字典类型 | 仍然自己定义 State 类型 |
| Node | 自己写函数并手动调用 | 自己写函数，用 add_node 注册 |
| Edge | 自己写 if/else | 用 add_edge / add_conditional_edges 注册 |
| 执行流程 | 自己写 run_graph | 用 graph.invoke |
| 分流逻辑 | 手动判断 next_node | route 函数返回节点名，框架执行 |

伪 Graph 里我们手写了：
if next_node == "list_documents_node":
    state = list_documents_node(state)
elif next_node == "read_document_node":
    state = read_document_node(state)
else:
    state = answer_question_node(state)

真实 LangGraph 中不需要手写这段，因为：
节点已经用 add_node 注册了。
条件边已经用 add_conditional_edges 注册了。
框架会根据 route_by_intent 的返回值自动执行对应节点。

State 类型仍然要自己定义。
Node 函数仍然要自己写。
Route 函数仍然要自己写。
业务逻辑仍然要自己设计。
LangGraph 只是帮我们管理流程，不会替我们理解业务。

test_langgraph_lists_documents
test_langgraph_reads_document
test_langgraph_answers_question
分别覆盖：
列文档路线
读文档路线
知识库问答路线
测试检查了：
intent
answer
steps

我的理解总结:
我现在理解 LangGraph 不是替我写 Agent，而是帮我组织 Agent 的流程。
我仍然需要自己定义 State、写 Node、写 Route 函数。
LangGraph 主要替代的是手写流程调度代码。
伪 Graph 帮我理解了底层逻辑，真实 LangGraph 则把这种逻辑框架化。

第二层条件分流:

第一层条件分流从 `decide_intent_node` 开始，根据 `intent` 选择路线。

第二层条件分流从 `search_context_node` 开始，根据 `has_context` 选择路线。

```text
search_context_node
  ↓
route_by_context
  ├── answer_node
  └── refuse_node

context 和 has_context 的区别:
context 保存证据内容。
has_context 表示是否找到了证据，是布尔值。
例如：
{
    "has_context": True,
    "context": "知识库证据片段"
}
表示找到证据。

{
    "has_context": False,
    "context": None
}
表示没有找到证据。

当前结束节点:
当前真正连到 END 的节点有 4 个：
list_documents_node
read_document_node
answer_node
refuse_node