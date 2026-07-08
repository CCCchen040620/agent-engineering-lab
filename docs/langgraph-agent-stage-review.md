# LangGraph Agent 阶段复盘

这份文档记录项目从手写 Simple Agent 迁移到 LangGraph Agent 的阶段成果。

它不是最终简历总结，而是一个阶段性学习复盘，用来确认我是否真正理解了：

- LangGraph 如何组织 Agent 流程
- State、Node、Edge 如何在真实项目中配合
- 如何把已有 Agent Tools 接入 LangGraph
- 如何通过测试和前端验收保证迁移过程安全

## 1. 当前阶段目标

这一阶段的目标是把手写 Simple Agent 的核心能力迁移到 LangGraph。

具体包括：

- 保留旧接口 `/api/v1/agent/chat`
- 新增 LangGraph 接口 `/api/v1/langgraph-agent/chat`
- 让两个接口可以并行对比，避免一次性替换造成风险
- 在 Streamlit 前端增加 “LangGraph Agent 问答” 选项
- 让 LangGraph Agent 支持文档列表、读取文档和知识库问答
- 增加上下文有效性校验，降低无关片段导致错误回答的风险
- 使用测试覆盖 service 层和 API 层

## 2. 当前 LangGraph Agent 支持的能力

当前 LangGraph Agent 已经支持三类意图：

| 意图 | 能力 | 示例问题 |
|---|---|---|
| `list_documents` | 查看知识库文档列表 | 知识库里有哪些文档？ |
| `read_document` | 读取指定文档 chunks | 查看员工手册的片段 |
| `answer_question` | 根据知识库问答 | 新员工什么时候完成安全培训？ |

额外能力：

- 无答案问题拒答
- embedding 召回无关片段时拒答
- 上下文有效性校验
- 引用来源返回
- Agent 执行步骤 `steps`
- FastAPI 接口演示
- Streamlit 前端切换演示

## 3. 当前核心文件

| 文件 | 作用 |
|---|---|
| `backend/services/langgraph_agent.py` | LangGraph Agent 的核心流程 |
| `backend/routers/langgraph_agent.py` | LangGraph Agent 的 FastAPI 接口 |
| `tests/test_langgraph_agent.py` | LangGraph Agent service 层测试 |
| `tests/test_backend_langgraph_agent.py` | LangGraph Agent API 层测试 |
| `frontend/api_client.py` | 前端调用 LangGraph Agent API |
| `frontend/streamlit_app.py` | Streamlit 页面切换 LangGraph Agent |
| `docs/api.md` | 记录 LangGraph Agent API 用法 |
| `docs/runbook.md` | 记录运行、验收和排错方法 |

## 4. LangGraph Agent 总体流程

当前流程可以理解为：

```text
用户问题
  ↓
decide_intent_node
  ↓
route_by_intent
  ├── list_documents_node
  ├── extract_document_title_node
  │       ↓
  │   route_by_document_title
  │       ├── ask_clarification_node
  │       └── find_document_node
  │               ↓
  │           route_by_document_found
  │               ├── ask_correct_title_node
  │               └── read_document_chunks_node
  └── search_knowledge_node
          ↓
      validate_context_node
          ↓
      route_by_context
          ├── answer_node
          └── refuse_node
```

这张图说明：

- Agent 先判断用户意图。
- 文档列表路线最简单。
- 读取文档路线需要多次分流。
- 知识库问答路线需要先检索，再判断上下文是否有效。
- 不是所有检索结果都可以直接拿来回答。

## 5. 三类意图的路线

### 5.1 文档列表路线

```text
decide_intent_node
  -> list_documents_node
  -> END
```

适合：

```text
知识库里有哪些文档？
```

该路线会调用：

```text
list_documents_tool
```

### 5.2 读取文档路线

成功读取：

```text
decide_intent_node
  -> extract_document_title_node
  -> find_document_node
  -> read_document_chunks_node
  -> END
```

适合：

```text
查看员工手册的片段
```

缺少标题：

```text
decide_intent_node
  -> extract_document_title_node
  -> ask_clarification_node
  -> END
```

适合：

```text
查看这份文档的片段
```

找不到文档：

```text
decide_intent_node
  -> extract_document_title_node
  -> find_document_node
  -> ask_correct_title_node
  -> END
```

读取文档路线比文档列表路线复杂，因为它需要处理：

- 是否能提取出标题
- 标题是否能匹配到真实文档
- 是否需要澄清
- 找到文档后如何读取 chunks
- 如何返回 citations

### 5.3 知识库问答路线

正常回答：

```text
decide_intent_node
  -> search_knowledge_node
  -> validate_context_node
  -> answer_node
  -> END
```

拒答：

```text
decide_intent_node
  -> search_knowledge_node
  -> validate_context_node
  -> refuse_node
  -> END
```

这条路线的关键不是“有 snippets 就回答”，而是：

```text
有 snippets，并且上下文通过校验，才回答。
```

## 6. `validate_context_node` 的作用

`validate_context_node` 是这一阶段很重要的新增节点。

之前的逻辑是：

```text
snippets 不为空 -> 回答
snippets 为空 -> 拒答
```

但这在 embedding 检索下不够安全。

例如用户问：

```text
公司有没有股票期权？
```

知识库里没有股票期权相关内容，但 embedding 检索可能召回：

- 设备借用制度
- 请假制度
- 远程办公制度

这些片段虽然被召回了，但不能支撑回答“股票期权”问题。

所以现在流程变成：

```text
search_knowledge_node
  -> validate_context_node
  -> answer_node/refuse_node
```

当前规则是：

```text
关键词必须出现在至少一个检索片段文本中，才认为上下文有效。
```

如果上下文无效：

```text
has_valid_context = false
```

就走：

```text
refuse_node
```

这个规则的价值是能降低“embedding 检索到无关片段也强行回答”的风险。

但它也有局限：

- 当前规则比较保守。
- 如果用户问“在家办公”，文档写“远程办公”，可能会误判为无效。
- 如果关键词提取不准确，也会影响校验结果。
- 后续可以升级为“分数阈值 + 关键词命中 + LLM 判断”的组合策略。

## 7. Simple Agent 和 LangGraph Agent 的区别

| 对比项 | Simple Agent | LangGraph Agent |
|---|---|---|
| 流程组织 | 普通 Python if/else | LangGraph `StateGraph` |
| 节点管理 | 手动调用函数 | `add_node` 注册节点 |
| 固定路线 | 手写函数调用 | `add_edge` |
| 条件分流 | `if/else` 判断 | `add_conditional_edges` |
| 多分支可读性 | 分支多了会变长 | 图结构更清楚 |
| 当前接口 | `/api/v1/agent/chat` | `/api/v1/langgraph-agent/chat` |
| 前端支持 | 已支持 | 已支持 |

我的理解：

```text
Simple Agent 更适合理解业务流程；
LangGraph Agent 更适合管理复杂状态和多分支流程。
```

LangGraph 没有替我写业务逻辑。

我仍然需要自己设计：

- State 里有什么字段
- Node 做什么
- Edge 根据什么分流
- 工具如何调用
- 什么情况下拒答

LangGraph 主要帮我管理：

- 节点之间的执行顺序
- 条件边的分流
- State 在节点之间的传递
- 后续扩展持久化、流式输出和人工介入的可能性

## 8. 这阶段新增测试

### 8.1 Service 层测试

文件：

```text
tests/test_langgraph_agent.py
```

覆盖：

- 文档列表
- 问答成功
- 无上下文拒答
- embedding 召回无关片段时拒答
- 成功读取文档 chunks
- 缺少文档标题时澄清
- 找不到文档时澄清正确标题

### 8.2 API 层测试

文件：

```text
tests/test_backend_langgraph_agent.py
```

覆盖：

- API 问答成功
- API 无上下文拒答
- API 成功读取文档 chunks
- API 缺少文档标题时澄清

API 测试中使用了：

```text
app.dependency_overrides
```

作用是：

- 使用临时测试数据库
- 避免污染真实 `data/app.db`
- 隔离真实 Ollama 调用
- 让测试更快、更稳定

## 9. 前端验收结果

### 9.1 无答案问题拒答

问题：

```text
公司有没有股票期权？
```

验收结果：

- embedding 检索命中 3 条
- `validate_context_node` 判断 `has_valid_context = false`
- 最终走 `refuse_answer_tool`
- citations 为空

前端步骤：

```text
[1] decide_agent_intent -> route_by_intent
[2] search_knowledge_base_tool -> validate_context
[3] validate_context_node -> refuse_node
[4] refuse_answer_tool -> finish
```

### 9.2 成功读取文档

问题：

```text
查看员工手册的片段
```

验收结果：

- 提取标题：员工手册
- 找到文档
- 读取 3 个 chunks
- 返回 3 条引用来源

前端步骤：

```text
[1] decide_agent_intent -> route_by_intent
[2] extract_document_title -> find_document_node
[3] find_document_by_title_tool -> read_document_chunks_node
[4] read_document_chunks_tool -> finish
```

### 9.3 缺少文档标题时澄清

问题：

```text
查看这份文档的片段
```

验收结果：

- 无法提取具体标题
- 返回“请补充文档标题。”
- citations 为空

前端步骤：

```text
[1] decide_agent_intent -> route_by_intent
[2] extract_document_title -> ask_clarification_node
[3] ask_clarification_tool -> finish
```

## 10. 这阶段踩过的坑

### 10.1 `return` 漏写 `graph.invoke(initial_state)`

现象：

```text
TypeError: 'NoneType' object is not subscriptable
```

原因：

```python
return
```

会返回 `None`。

正确写法：

```python
return graph.invoke(initial_state)
```

### 10.2 LangGraph 边连接错误

现象：

```text
keyword 一直是空字符串
```

原因：

- 忘记从 `decide_intent_node` 添加第一层条件边。
- 流程只执行了意图判断，没有走到后续节点。

正确思路：

```text
decide_intent_node
  -> route_by_intent
  -> list_documents_node / extract_document_title_node / search_knowledge_node
```

### 10.3 新增节点后测试 steps 顺序要更新

新增 `validate_context_node` 后，流程从：

```text
search_knowledge_node -> answer_node/refuse_node
```

变成：

```text
search_knowledge_node -> validate_context_node -> answer_node/refuse_node
```

所以：

```text
answer_with_context_tool
refuse_answer_tool
```

都从第 3 步变成了第 4 步。

测试也必须同步更新。

### 10.4 `uvicorn --reload` 旧进程残留

现象：

- 直接调用 Python 函数是新逻辑。
- 但 `/docs` 或 Streamlit 页面还是旧逻辑。
- 例如代码中已经有 `validate_context_node`，但 API 返回的 `steps` 里没有这一项。

解决：

1. 停掉旧 FastAPI 进程。
2. 确认 8000 端口空了。
3. 用不带 `--reload` 的方式干净启动一次验证。

```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

### 10.5 Service 层通过，不代表 API 和前端一定通过

这一阶段出现过：

- service 层直接调用有 citations
- 但 API 返回 citations 为空

原因仍然是运行中的后端进程没有加载最新代码。

这说明验收应该分层：

```text
service 测试
API 测试
前端手动验收
```

三层都过，才算真的可用。

## 11. 当前局限

当前 LangGraph Agent 还不是最终形态。

主要局限：

- `validate_context_node` 规则还比较简单。
- 关键词校验不适合所有语义检索场景。
- `read_document` 的标题提取仍然是规则式。
- 还没有 LangGraph checkpoint / memory。
- 还没有持久化 Agent 状态。
- 还没有流式 LangGraph 输出。
- 还没有人工确认节点。
- 还没有把旧 Simple Agent 替换为 LangGraph Agent。

这些不是当前阶段必须解决的问题，但可以作为下一阶段方向。

## 12. 下一步计划

建议下一步做：

1. 优化 `validate_context_node`，加入更稳健的上下文有效性判断。
2. 改进文档标题提取能力。
3. 学习 LangGraph checkpoint / memory。
4. 学习 LangGraph 流式输出。
5. 增加人工确认节点。
6. 等 LangGraph Agent 更稳定后，再考虑是否替换旧 `/api/v1/agent/chat`。
7. 最后再做阶段性 README、项目截图、演示视频和简历总结。

## 13. 我的理解总结

我现在理解 LangGraph 不是帮我自动写 Agent，而是帮我组织 Agent 的流程。

业务逻辑仍然需要我自己设计，包括 State 字段、节点职责、条件边和工具调用。

LangGraph 的价值在于：当 Agent 流程变复杂时，它能让多分支流程更清楚。

在这个项目里，读取文档和知识库问答都不是简单的一步函数，而是包含多个判断和分支。

如果继续用普通 Python 手写，代码会越来越长；用 LangGraph 后，每个节点职责更单一，流程也更容易解释。

企业级 Agent 需要可解释流程，因为出错时必须知道问题发生在意图判断、工具调用、检索、上下文校验还是回答生成。

这也是 `steps` 字段的重要价值：它让 Agent 的执行过程可观察、可调试、可验收。
