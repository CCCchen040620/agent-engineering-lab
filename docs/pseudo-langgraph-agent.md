# 伪 LangGraph Agent 学习笔记

这份文档记录我用普通 Python 模拟 LangGraph 的过程。

当前练习文件：

```text
week09/pseudo_langgraph_agent.py
```

它不是正式的 LangGraph 代码，而是一个教学版 Graph，用来理解 LangGraph 的核心思想：

```text
State -> Node -> Edge -> Graph
```

## 1. 为什么要先写伪 LangGraph

在直接学习 LangGraph 之前，我先用普通 Python 手写一个类似的流程。

这样做的好处是：

- 不会一开始就被框架语法干扰。
- 可以先理解 Agent 工作流的本质。
- 可以看清楚 State、Node、Edge 分别负责什么。
- 后面迁移到 LangGraph 时，知道框架到底帮我省掉了哪些代码。

也就是说，伪 LangGraph 的目的不是替代 LangGraph，而是先把底层思想讲清楚。

## 2. State 是什么

State 是 Agent 工作过程中的“任务记录本”。

当前 `AgentState` 包含：

| 字段 | 含义 |
|---|---|
| `question` | 用户原始问题 |
| `intent` | Agent 判断出的用户意图 |
| `has_context` | 是否找到了知识库证据 |
| `context` | 找到的知识库上下文 |
| `answer` | 最终回答 |
| `steps` | Agent 执行步骤记录 |

State 不是只保存最终答案，而是保存整个执行过程中的关键信息。

例如，当用户问：

```text
员工可以远程办公吗？
```

Graph 执行过程中，State 会逐步被补充：

```text
question -> intent -> has_context -> context -> answer -> steps
```

所以可以这样理解：

```text
State = Agent 当前已经知道的信息
```

## 3. Node 是什么

Node 是一个处理步骤。

在当前伪 Graph 里，Node 的共同特点是：

```text
输入 State
修改 State
返回 State
```

当前 Node 包括：

| Node | 作用 |
|---|---|
| `decide_intent_node` | 判断用户意图 |
| `list_documents_node` | 模拟列出知识库文档 |
| `read_document_node` | 模拟读取文档内容 |
| `search_context_node` | 模拟搜索知识库证据 |
| `answer_node` | 有证据时生成回答 |
| `refuse_node` | 无证据时拒答 |

判断一个函数是不是 Node，关键不是看它是不是 `def`，而是看它的职责。

如果它负责处理业务，并且会修改 State，它就更像 Node。

例如：

```python
def answer_node(state: AgentState) -> AgentState:
    state["steps"].append("知识库问答")
    state["answer"] = "这是根据知识库生成的回答"
    return state
```

这个函数会修改 `steps` 和 `answer`，所以它是 Node。

## 4. Edge 是什么

Edge 是路线选择规则。

在当前伪 Graph 里，Edge 的共同特点是：

```text
读取 State
根据条件返回下一站名字
不直接处理业务
```

当前 Edge 包括：

| Edge | 作用 |
|---|---|
| `route_by_intent` | 根据用户意图决定走哪条任务路线 |
| `route_by_context` | 根据是否有知识库证据决定回答还是拒答 |

判断一个函数是不是 Edge，关键看它是否负责决定下一步去哪。

例如：

```python
def route_by_context(state: AgentState) -> str:
    if state["has_context"]:
        return "answer_node"

    return "refuse_node"
```

这个函数没有生成回答，也没有读取文档，只是根据 `has_context` 返回下一站名字，所以它是 Edge。

我可以用一句话区分：

```text
改 State 的，是 Node。
选路线的，是 Edge。
```

## 5. 当前 Graph 流程

当前流程可以理解为：

```text
用户问题
  ↓
create_initial_state
  ↓
decide_intent_node
  ↓
route_by_intent
  ├── list_documents_node
  ├── read_document_node
  └── search_context_node
          ↓
      route_by_context
          ├── answer_node
          └── refuse_node
```

这张流程图说明：

- Agent 不是一上来就回答。
- Agent 会先判断用户意图。
- 如果是普通问答，还会先搜索上下文。
- 如果有证据，就回答。
- 如果没有证据，就拒答。

## 6. 两层分流

当前伪 Graph 有两层分流。

第一层分流：

```text
根据用户意图分流
```

也就是：

```text
list_documents
read_document
answer_question
```

第二层分流：

```text
在 answer_question 内部，根据是否有知识库证据分流
```

也就是：

```text
有证据 -> answer_node
无证据 -> refuse_node
```

这说明 Agent 不只是“判断用户想做什么”，还要根据工具结果继续决定下一步。

这个思想在真实 Agent 中很重要，因为真实流程里经常会出现：

- 检索成功后回答
- 检索失败后拒答
- 参数缺失时澄清
- 工具调用失败时降级
- 命中多个结果时要求用户确认

## 7. `run_graph` 的作用

当前手写版里，`run_graph` 扮演的是 Graph 执行器。

它负责：

1. 创建初始 State。
2. 执行判断意图 Node。
3. 调用 Edge 决定下一站。
4. 根据下一站执行对应 Node。
5. 返回最终 State。

所以它模拟的是：

```text
graph.invoke(...)
```

只是现在还没有真正使用 LangGraph，所以流程执行代码需要自己手写。

## 8. 手写伪 Graph 和真实 LangGraph 的区别

当前手写代码里，`run_graph` 需要自己写类似这样的逻辑：

```python
if next_node == "list_documents_node":
    state = list_documents_node(state)
elif next_node == "read_document_node":
    state = read_document_node(state)
else:
    state = search_context_node(state)
    context_next_node = route_by_context(state)

    if context_next_node == "answer_node":
        state = answer_node(state)
    else:
        state = refuse_node(state)
```

真实 LangGraph 会把节点和边注册到图里，然后由框架自动执行。

所以可以理解为：

| 当前伪 Graph | 真实 LangGraph |
|---|---|
| 手动创建 State | 定义 State 类型 |
| 手动调用 Node | 注册 Node |
| 手动写 `if/else` 路由 | 注册 Conditional Edge |
| 手动执行 `run_graph` | 调用 `graph.invoke(...)` |
| 手动维护流程 | 框架管理流程 |

真实 LangGraph 主要帮我们管理：

- 节点之间怎么流转
- 条件分支怎么选择
- State 怎么在节点之间传递
- 中间过程怎么追踪
- 后续如何扩展持久化、流式输出和人工介入

## 9. 和当前正式 Simple Agent 的关系

当前正式项目里已经有：

```text
backend/services/simple_agent.py
```

它是一个可以接入真实工具、真实数据库、真实 API 的 Simple Agent。

而 `week09/pseudo_langgraph_agent.py` 是教学练习文件。

两者关系可以这样理解：

| 文件 | 作用 |
|---|---|
| `backend/services/simple_agent.py` | 正式 Simple Agent，实现真实业务流程 |
| `week09/pseudo_langgraph_agent.py` | 教学版伪 Graph，用来理解 LangGraph 思想 |

伪 Graph 的价值是把复杂业务先简化，让我看清楚：

```text
State、Node、Edge、Graph 是怎么配合工作的
```

## 10. 我现在对 LangGraph 的理解

LangGraph 不是魔法。

它本质上是在帮开发者管理：

- 状态如何保存
- 节点如何执行
- 条件如何分流
- 流程如何流转
- 中间过程如何追踪

我现在写的伪 Graph，是为了理解 LangGraph 的底层思想。

下一步真正使用 LangGraph 时，我需要重点关注：

- 如何定义 State
- 如何写 Node 函数
- 如何添加普通 Edge
- 如何添加 Conditional Edge
- 如何执行 Graph

## 11. 当前阶段自测问题

1. State 是最终答案，还是过程记录？
2. Node 的核心职责是什么？
3. Edge 的核心职责是什么？
4. 为什么 `route_by_context` 是 Edge，而不是 Node？
5. 为什么要把 `answer_node` 和 `refuse_node` 拆开？
6. `run_graph` 在当前伪 Graph 里扮演什么角色？
7. 真实 LangGraph 会帮我们省掉哪部分手写代码？
8. 为什么最后返回整个 State，而不是只返回 answer？
9. 当前伪 Graph 和正式 Simple Agent 的区别是什么？
10. 如果未来要加入“人工确认”，应该更像新增 Node，还是只改 answer？
