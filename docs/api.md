## 当前可用 API

启动后端：

```powershell
python -m uvicorn backend.main:app --reload
```

接口文档：

```text
http://127.0.0.1:8000/docs
```

### 基础接口

- `GET /health`：健康检查
- `GET /api/v1/info`：系统信息与功能列表
- `GET /api/v1/system/status`：系统诊断，检查 API、SQLite、Ollama、LLM 模型和 Embedding 模型状态

### 错误响应格式

后端错误响应会保留 FastAPI 常见的 `detail` 字段，同时增加统一的 `error` 和 `request_id` 字段。

示例：

```json
{
  "detail": "文档不存在。",
  "error": {
    "code": "not_found",
    "message": "文档不存在。",
    "status_code": 404
  },
  "request_id": "..."
}
```

说明：

- `detail`：保留旧格式，兼容已有测试和前端逻辑。
- `error.code`：程序更适合读取的错误类型，例如 `not_found`、`conflict`、`validation_error`、`rate_limited`。
- `error.message`：适合展示给用户看的错误说明。
- `request_id`：本次请求编号，可用于结合后端日志排查问题。

### 问答接口

- `POST /api/v1/chat`：根据企业知识库回答问题，并返回引用来源

请求示例：

```json
{
  "question": "差旅报销多久内提交？"
}
```

## JSON 文档接口（Legacy）
> 说明：这组接口使用 `data/documents.json` 保存文档数据，是早期学习阶段实现的旧版接口。当前推荐使用 SQLite 文档接口。

- `GET /api/v1/documents`：查看文档列表
- `GET /api/v1/documents?indexed_only=true`：只查看已索引文档
- `GET /api/v1/documents?file_type=pdf`：按文件类型筛选
- `GET /api/v1/documents/by-id/{document_id}`：按 id 查看文档
- `POST /api/v1/documents`：新增文档
- `DELETE /api/v1/documents/by-id/{document_id}`：按 id 删除文档

## SQLite 文档接口
> 说明：这组接口使用 `data/app.db` 保存文档数据，是当前推荐的主线文档接口。

SQLite 版接口使用本地数据库 `data/app.db` 保存文档数据。

### GET /api/v1/db/documents

查看 SQLite 文档列表。

支持查询参数：

- `indexed_only=true`：只查看已索引文档
- `file_type=md`：按文件类型筛选

### GET /api/v1/db/documents/{document_id}

按 id 查看 SQLite 文档。

### POST /api/v1/db/documents

新增 SQLite 文档。

请求示例：

```json
{
  "title": "请假制度",
  "file_type": "md",
  "chunk_count": 5,
  "is_indexed": true
}
```

成功返回状态码：

```text
201 Created
```

标题重复时返回：

```text
409 Conflict
```

### DELETE /api/v1/db/documents/{document_id}

按 id 删除 SQLite 文档。

成功返回示例：

```json
{
  "message": "文档已删除。",
  "id": 2
}
```

### GET /api/v1/db/documents/{document_id}/chunks

查看某个 SQLite 文档切分后的 chunks。

示例：

```text
GET /api/v1/db/documents/6/chunks

返回示例：

[
  {
    "id": 1,
    "document_id": 6,
    "text": "员工可以远程办公吗。"
  },
  {
    "id": 2,
    "document_id": 6,
    "text": "可以。"
  }
]

如果文档不存在，返回：

404 Not Found

说明：RAG 检索实际使用的是 chunks，而不是整篇文档。该接口可用于调试文档切分和检索质量。

### POST /api/v1/db/documents/upload-text

上传 `.txt` 文件，并自动完成文档入库、chunks 切分和 embeddings 生成。

限制：

- 文档标题默认最多 `100` 个字符。
- 上传文件默认最大 `1048576` 字节，约 1MB。

如果本地 Embedding 模型不可用，接口会返回 `503 Service Unavailable`，并提示确认 Ollama 和 `bge-m3` 已启动。

请求类型：

```text
multipart/form-data

## SQLite 问答接口
> 说明：这是当前推荐的问答接口，基于 SQLite `chunks` 表检索片段并返回引用来源。

### POST /api/v1/db/chat

从 SQLite `chunks` 表检索文档片段，并生成带引用来源的回答。

请求示例：

```json
{
  "question": "新员工什么时候完成安全培训？"
}

支持查询参数：

- `top_k`：最多返回几个引用片段，默认 `3`，范围 `1` 到 `5`
- `mode`：检索模式，默认 `keyword`
- `keyword`：使用 SQLite `LIKE` 关键词检索
- `vector`：使用 jieba 分词、词频向量和余弦相似度检索

示例：

```text
POST /api/v1/db/chat?top_k=2
POST /api/v1/db/chat?mode=vector&top_k=2
```

返回示例：

```json
{
  "question": "新员工什么时候完成安全培训？",
  "keyword": "安全培训",
  "answer": "根据知识库资料：...",
  "citations": [
    {
      "title": "员工手册",
      "text": "新员工入职后需要在 30 天内完成安全培训。",
      "path": "sqlite://1"
    }
  ]
}
```

### POST /api/v1/db/chat/llm

使用 SQLite `chunks` 表检索文档片段，构造 RAG Prompt，并调用本地 Ollama/Qwen 生成回答。

请求示例：

```json
{
  "question": "新员工什么时候完成安全培训？"
}

返回示例：

{
  "question": "新员工什么时候完成安全培训？",
  "keyword": "安全培训",
  "answer": "新员工需要在入职后30天内完成安全培训。",
  "citations": [
    {
      "title": "员工手册",
      "text": "新员工入职后需要在 30 天内完成安全培训。",
      "path": "sqlite://1"
    }
  ]
}

支持查询参数：

- `top_k`：最多返回几个引用片段，默认 `3`
- `mode`：检索模式，支持 `keyword`、`vector`、`embedding`
- `mode=keyword`：使用 SQLite `LIKE` 关键词检索
- `mode=vector`：使用 jieba 分词、词频向量和余弦相似度检索
- `mode=embedding`：使用 Ollama `bge-m3` 生成语义向量，并用余弦相似度检索 chunks
- `min_score`：相似度最低门槛，默认 `0.3`

检索模式说明：

- `keyword`：使用 SQLite `LIKE` 做关键词检索，速度快、可解释，但对自然语言表达变化不敏感。
- `vector`：使用 jieba 分词、词频向量和余弦相似度检索，适合学习向量检索原理。
- `embedding`：使用 Ollama `bge-m3` 生成语义向量，并通过余弦相似度检索 chunks。该模式语义能力更强，但会实时调用本地 embedding 模型，速度相对较慢。
- `precomputed_embedding`：使用入库时预先保存的 chunk embedding 检索。查询时只计算用户问题的 embedding，速度通常快于实时 `embedding` 模式。

调参说明：

- `top_k` 控制最多返回几个候选片段。
- `min_score` 控制最低相似度门槛。
- 较低的 `min_score` 会提高召回率，但可能引入弱相关片段。
- 较高的 `min_score` 会减少噪声，但可能漏掉有用片段。

异常降级说明：

当本地 Ollama/Qwen 服务不可用、超时或生成失败时，接口不会直接崩溃，而是返回友好提示：

```json
{
  "answer": "本地模型暂时不可用，请稍后再试。"
}

## Agent 接口

### POST /api/v1/agent/chat

运行第一版简单 Agent 流程。

该接口会执行：

1. 判断用户意图
2. 如果是文档列表类问题，则调用 `list_documents_tool`
3. 如果是读取文档类问题，则提取文档标题并调用 `find_document_by_title_tool` 和 `read_document_chunks_tool`
4. 如果读取文档类问题缺少文档标题，则调用 `ask_clarification_tool`
5. 如果是普通问答，则调用 `search_knowledge_base_tool`
6. 如果普通问答检索到片段，则调用 `answer_with_context_tool`
7. 如果普通问答没有检索到片段，则调用 `refuse_answer_tool`
8. 返回回答、引用来源和执行步骤

请求示例：

```json
{
  "question": "新员工什么时候完成安全培训？"
}
```

文档列表类请求示例：

```json
{
  "question": "知识库里有哪些文档？"
}
```

读取文档类请求示例：

```json
{
  "question": "查看员工手册的片段"
}
```

缺少文档标题时的请求示例：

```json
{
  "question": "查看这份文档的片段"
}
```

可选查询参数：

- `top_k`：最多使用几个检索片段，默认 `3`，范围 `1-5`
- `mode`：检索模式，默认 `keyword`
- `min_score`：最低相似度分数，默认读取项目配置

示例：

```text
POST /api/v1/agent/chat?mode=keyword&top_k=3
```

返回示例：

```json
{
  "question": "新员工什么时候完成安全培训？",
  "keyword": "安全培训",
  "answer": "新员工需要在入职后 30 天内完成安全培训。",
  "citations": [
    {
      "title": "员工手册",
      "text": "新员工入职后需要在 30 天内完成安全培训。",
      "path": "sqlite://1"
    }
  ],
  "steps": [
    {
      "step": 1,
      "tool": "decide_agent_intent",
      "input": {
        "question": "新员工什么时候完成安全培训？"
      },
      "observation": {
        "intent": "answer_question"
      },
      "next_action": "search_knowledge_base"
    },
    {
      "step": 2,
      "tool": "search_knowledge_base_tool",
      "input": {
        "question": "新员工什么时候完成安全培训？",
        "mode": "keyword",
        "top_k": 3,
        "min_score": 0.3
      },
      "observation": {
        "keyword": "安全培训",
        "result_count": 1
      },
      "next_action": "answer_with_context"
    },
    {
      "step": 3,
      "tool": "answer_with_context_tool",
      "input": {
        "snippet_count": 1
      },
      "observation": {
        "citation_count": 1
      },
      "next_action": "finish"
    }
  ]
}
```

文档列表类返回示例：

```json
{
  "question": "知识库里有哪些文档？",
  "keyword": "文档列表",
  "answer": "知识库中有这些文档：员工手册、请假制度",
  "citations": [],
  "steps": [
    {
      "step": 1,
      "tool": "decide_agent_intent",
      "input": {
        "question": "知识库里有哪些文档？"
      },
      "observation": {
        "intent": "list_documents"
      },
      "next_action": "list_documents"
    },
    {
      "step": 2,
      "tool": "list_documents_tool",
      "input": {},
      "observation": {
        "document_count": 2,
        "document_titles": ["员工手册", "请假制度"]
      },
      "next_action": "finish"
    }
  ]
}
```

读取文档类返回示例：

```json
{
  "question": "查看员工手册的片段",
  "keyword": "员工手册",
  "answer": "员工手册 的片段如下：\n[1] 员工每天需要完成 8 小时工作。\n[2] 新员工需要完成安全培训。",
  "citations": [
    {
      "title": "员工手册",
      "text": "员工每天需要完成 8 小时工作。",
      "path": "sqlite://1"
    },
    {
      "title": "员工手册",
      "text": "新员工需要完成安全培训。",
      "path": "sqlite://1"
    }
  ],
  "steps": [
    {
      "step": 1,
      "tool": "decide_agent_intent",
      "input": {
        "question": "查看员工手册的片段"
      },
      "observation": {
        "intent": "read_document"
      },
      "next_action": "extract_document_title"
    },
    {
      "step": 2,
      "tool": "extract_document_title",
      "input": {
        "question": "查看员工手册的片段"
      },
      "observation": {
        "document_title": "员工手册"
      },
      "next_action": "find_document_by_title"
    },
    {
      "step": 3,
      "tool": "find_document_by_title_tool",
      "input": {
        "title": "员工手册"
      },
      "observation": {
        "found": true,
        "document_id": 1,
        "match_type": "exact"
      },
      "next_action": "read_document_chunks"
    },
    {
      "step": 4,
      "tool": "read_document_chunks_tool",
      "input": {
        "document_id": 1
      },
      "observation": {
        "chunk_count": 2
      },
      "next_action": "finish"
    }
  ]
}
```

缺少文档标题时的返回示例：

```json
{
  "question": "查看这份文档的片段",
  "keyword": "文档标题",
  "answer": "请补充文档标题。",
  "citations": [],
  "steps": [
    {
      "step": 1,
      "tool": "decide_agent_intent",
      "input": {
        "question": "查看这份文档的片段"
      },
      "observation": {
        "intent": "read_document"
      },
      "next_action": "extract_document_title"
    },
    {
      "step": 2,
      "tool": "extract_document_title",
      "input": {
        "question": "查看这份文档的片段"
      },
      "observation": {
        "document_title": "",
        "missing_field": "文档标题"
      },
      "next_action": "ask_clarification"
    },
    {
      "step": 3,
      "tool": "ask_clarification_tool",
      "input": {
        "missing_field": "文档标题"
      },
      "observation": {
        "answer": "请补充文档标题。"
      },
      "next_action": "finish"
    }
  ]
}
```

说明：

- 这是项目中的第一版 Agent 流程。
- 当前支持三类意图：`list_documents`、`read_document` 和 `answer_question`。
- 当前还没有使用 LangGraph，而是用普通 Python 函数手写决策流程。
- `steps` 字段用于展示 Agent 的执行过程，包括工具名、工具输入、观察结果和下一步动作。
- 当前支持的文档列表类问法包括：“知识库里有哪些文档？”、“请列出文档”、“查看文档列表”。
- 当前支持的读取文档类问法包括：“查看员工手册的片段”、“读取请假制度的内容”、“员工手册有哪些内容”。
- 读取文档时，`find_document_by_title_tool` 的 `match_type` 表示标题匹配方式：
  - `exact`：文档标题精确匹配，例如“员工手册”匹配“员工手册”
  - `contains`：用户输入是文档标题的一部分，例如“手册”匹配“员工手册”
  - `null`：没有找到匹配文档
- 当读取文档类问题缺少明确文档标题时，Agent 会调用 `ask_clarification_tool` 进行澄清。
- 后续可以把这个流程迁移到 LangGraph 状态图。

### POST /api/v1/langgraph-agent/chat

运行 LangGraph 版本的 Agent 流程。

这是项目中用于对照和迁移的新接口，不会替换原来的 `/api/v1/agent/chat`。

当前该接口会执行：

1. 使用 `decide_agent_intent` 判断用户意图
2. 如果是文档列表类问题，则调用 `list_documents_tool`
3. 如果是读取文档类问题，则调用 `extract_document_title`、`find_document_by_title_tool` 和 `read_document_chunks_tool`
4. 如果读取文档类问题缺少文档标题，或找不到文档，则调用 `ask_clarification_tool`
5. 如果是普通问答，则调用 `search_knowledge_base_tool`
6. 调用 `validate_context_node` 判断检索片段是否真的包含有效上下文
7. 如果上下文有效，则调用 `answer_with_context_tool`
8. 如果上下文无效，则调用 `refuse_answer_tool`
9. 返回回答、引用来源和 LangGraph 执行步骤

请求示例：

```json
{
  "question": "新员工什么时候完成安全培训？"
}
```

可选查询参数：

- `top_k`：最多使用几个检索片段，默认 `3`，范围 `1-5`
- `mode`：检索模式，默认 `keyword`
- `min_score`：最低相似度分数，默认读取项目配置

示例：

```text
POST /api/v1/langgraph-agent/chat?mode=keyword&top_k=3
```

返回示例：

```json
{
  "question": "新员工什么时候完成安全培训？",
  "intent": "answer_question",
  "keyword": "安全培训",
  "answer": "新员工需要在入职后 30 天内完成安全培训。",
  "citations": [
    {
      "title": "员工手册",
      "text": "新员工入职后需要在 30 天内完成安全培训。",
      "path": "sqlite://1"
    }
  ],
  "steps": [
    {
      "step": 1,
      "tool": "decide_agent_intent",
      "input": {
        "question": "新员工什么时候完成安全培训？"
      },
      "observation": {
        "intent": "answer_question"
      },
      "next_action": "route_by_intent"
    },
    {
      "step": 2,
      "tool": "search_knowledge_base_tool",
      "input": {
        "question": "新员工什么时候完成安全培训？",
        "top_k": 3,
        "mode": "keyword",
        "min_score": 0.3
      },
      "observation": {
        "keyword": "安全培训",
        "result_count": 1
      },
      "next_action": "validate_context"
    },
    {
      "step": 3,
      "tool": "validate_context_node",
      "input": {
        "keyword": "安全培训",
        "snippet_count": 1
      },
      "observation": {
        "has_valid_context": true
      },
      "next_action": "answer_node"
    },
    {
      "step": 4,
      "tool": "answer_with_context_tool",
      "input": {
        "question": "新员工什么时候完成安全培训？",
        "snippet_count": 1
      },
      "observation": {
        "citation_count": 1
      },
      "next_action": "finish"
    }
  ]
}
```

文档列表类请求示例：

```json
{
  "question": "知识库里有哪些文档？"
}
```

该类问题会走：

```text
decide_intent_node -> list_documents_node -> END
```

读取文档类请求示例：

```json
{
  "question": "查看员工手册的片段"
}
```

该类问题会走：

```text
decide_intent_node -> extract_document_title_node -> find_document_node -> read_document_chunks_node -> END
```

读取文档类返回示例：

```json
{
  "question": "查看员工手册的片段",
  "intent": "read_document",
  "keyword": "员工手册",
  "document_title": "员工手册",
  "answer": "员工手册 的片段如下：\n[1] 员工每天需要完成 8 小时工作。\n[2] 新员工入职后需要在 30 天内完成安全培训。",
  "citations": [
    {
      "title": "员工手册",
      "text": "员工每天需要完成 8 小时工作。",
      "path": "sqlite://1"
    },
    {
      "title": "员工手册",
      "text": "新员工入职后需要在 30 天内完成安全培训。",
      "path": "sqlite://1"
    }
  ],
  "steps": [
    {
      "step": 1,
      "tool": "decide_agent_intent",
      "observation": {
        "intent": "read_document"
      },
      "next_action": "route_by_intent"
    },
    {
      "step": 2,
      "tool": "extract_document_title",
      "observation": {
        "document_title": "员工手册",
        "missing_field": ""
      },
      "next_action": "find_document_node"
    },
    {
      "step": 3,
      "tool": "find_document_by_title_tool",
      "observation": {
        "found": true,
        "document_id": 1,
        "match_type": "exact"
      },
      "next_action": "read_document_chunks_node"
    },
    {
      "step": 4,
      "tool": "read_document_chunks_tool",
      "observation": {
        "chunk_count": 2
      },
      "next_action": "finish"
    }
  ]
}
```

如果读取文档类问题缺少标题，则会走：

```text
decide_intent_node -> extract_document_title_node -> ask_clarification_node -> END
```

普通问答类问题会走：

```text
decide_intent_node -> search_knowledge_node -> validate_context_node -> answer_node/refuse_node -> END
```

说明：

- 这是项目中的 LangGraph 版本 Agent 流程。
- 当前支持三类主要路线：`list_documents`、`read_document` 和 `answer_question`。
- 该接口复用了真实 Agent Tools，包括 `list_documents_tool`、`find_document_by_title_tool`、`read_document_chunks_tool`、`search_knowledge_base_tool`、`answer_with_context_tool` 和 `refuse_answer_tool`。
- `validate_context_node` 用于降低“embedding 检索命中了无关片段也强行回答”的风险。
- 当前上下文校验规则比较保守：关键词需要出现在至少一个检索片段文本中，后续可以升级为更稳健的语义相关性判断。
- 与手写 Simple Agent 相比，该接口使用 LangGraph 的 `StateGraph`、`add_node`、`add_edge` 和 `add_conditional_edges` 管理流程。
- 保留旧接口是为了安全迁移和对比测试，避免一次性替换造成回归风险。

### POST /api/v1/langgraph-agent/conversations/{conversation_id}/chat

运行带会话存储的 LangGraph Agent 聊天接口。

该接口会：

1. 检查 conversation 是否存在
2. 读取已有 messages 和 conversation summary
3. 调用 LangGraph Agent
4. 将用户问题保存为 `user` 消息
5. 将 Agent 回答保存为 `assistant` 消息
6. 根据最新 messages 生成新的 conversation summary
7. 写回 `conversations.summary`
8. 返回 Agent 结果、本轮保存的消息和新的 `conversation_summary`

请求示例：

```text
POST /api/v1/langgraph-agent/conversations/1/chat?mode=keyword&top_k=3
```

请求体：

```json
{
  "question": "公司有没有股票期权？"
}
```

成功返回示例：

```json
{
  "question": "公司有没有股票期权？",
  "intent": "answer_question",
  "keyword": "股票期权",
  "answer": "知识库中没有找到相关资料，暂时无法回答。",
  "citations": [],
  "conversation_id": 1,
  "conversation_summary": "最近问题：公司有没有股票期权？。",
  "saved_messages": [
    {
      "id": 1,
      "conversation_id": 1,
      "role": "user",
      "content": "公司有没有股票期权？"
    },
    {
      "id": 2,
      "conversation_id": 1,
      "role": "assistant",
      "content": "知识库中没有找到相关资料，暂时无法回答。"
    }
  ]
}
```

如果会话不存在，返回：

```json
{
  "detail": "会话不存在。"
}
```

说明：

- 该接口是带会话消息存储的 LangGraph Agent 实验接口。
- 它不会替换 `/api/v1/langgraph-agent/chat`。
- `/api/v1/langgraph-agent/chat` 是无会话版本。
- `/api/v1/langgraph-agent/conversations/{conversation_id}/chat` 会把本轮 user/assistant 消息保存到 SQLite。
- Streamlit 用户问答页在选择 `LangGraph Agent 问答` 并勾选 `保存 LangGraph Agent 问答到会话` 时，会调用该接口。
- 返回中的 `saved_messages` 会被前端用于显示本轮实际保存了几条消息。
- 当前接口会读取该 `conversation_id` 下已有的 messages 和 summary，并用于有限的上下文增强。
- assistant 消息会在 `metadata` 中保存 `intent`、`keyword`、`citations` 和 `steps`。
- 如果历史 assistant 消息或 summary 里有最近引用文档，后续问题会尝试基于最近引用文档构造 `contextual_question`。
- 当最近引用文档存在时，检索结果会优先过滤到该文档，减少无关引用混入。
- 如果当前问题和历史上下文不相关，Agent 会拒答，避免被旧上下文带偏。
- summary 只用于辅助检索方向，不能直接作为最终回答依据。
- 这还不是完整长期记忆：当前没有用户画像、跨会话记忆，也没有把全部历史内容交给模型自由推理。
- 它和 Memory Demo API 不同：Memory Demo 使用 `InMemorySaver`，重启会丢；该接口把消息写入 SQLite，重启后消息仍然存在。

### POST /api/v1/memory-demo/chat

运行 LangGraph memory/checkpoint 教学接口。

该接口用于演示：

```text
同一个 thread_id 可以接上之前的 State。
不同 thread_id 之间互相隔离。
```

请求示例：

```text
POST /api/v1/memory-demo/chat?thread_id=chen
```

请求体：

```json
{
  "question": "我叫陈晨"
}
```

返回示例：

```json
{
  "messages": ["我叫陈晨"],
  "remembered_name": "陈晨",
  "answer": "我记住了，你叫陈晨。",
  "steps": ["remember_name: 我叫陈晨"]
}
```

再次使用同一个 `thread_id` 请求：

```json
{
  "question": "我叫什么？"
}
```

返回示例：

```json
{
  "messages": ["我叫陈晨", "我叫什么？"],
  "remembered_name": "陈晨",
  "answer": "你叫陈晨。",
  "steps": [
    "remember_name: 我叫陈晨",
    "recall_name: 我叫什么？"
  ]
}
```

如果换成另一个 `thread_id`：

```text
POST /api/v1/memory-demo/chat?thread_id=other
```

再问：

```json
{
  "question": "我叫什么？"
}
```

会返回：

```json
{
  "messages": ["我叫什么？"],
  "remembered_name": null,
  "answer": "我还不知道你的名字。",
  "steps": ["missing_memory: 我叫什么？"]
}
```

说明：

- `thread_id` 相当于会话 ID。
- 该接口使用 `InMemorySaver`，只适合本地学习和演示。
- 后端进程重启后，内存中的记忆会消失。
- 当前接口不是正式企业知识库 Agent 的长期记忆方案。
- 正式项目后续可以结合 `Conversation`、`Message` 和数据库持久化实现长期会话记忆。

## Conversation 接口

Conversation 接口用于保存会话、消息和会话级摘要。

当前 LangGraph Agent 的带会话接口已经会读取并更新 `summary`。`summary` 是对一个 conversation 的简短记忆摘要。

### POST /api/v1/conversations

创建一个新会话。

请求示例：

```json
{
  "title": "第一次对话"
}
```

成功返回：

```json
{
  "id": 1,
  "title": "第一次对话",
  "summary": ""
}
```

说明：

- `title` 不能为空。
- 返回的 `id` 后续可以作为会话 ID 使用。
- 未来可以把 `conversation_id` 转成 LangGraph 的 `thread_id`。

### GET /api/v1/conversations

查看会话列表。

返回示例：

```json
[
  {
    "id": 1,
    "title": "第一次对话",
    "summary": "最近问题：公司有没有股票期权？。"
  },
  {
    "id": 2,
    "title": "第二次对话",
    "summary": ""
  }
]
```

说明：

- 该接口适合前端展示历史会话列表。

### GET /api/v1/conversations/{conversation_id}

查看单个会话详情。

返回示例：

```json
{
  "id": 1,
  "title": "第一次对话",
  "summary": "最近问题：公司有没有股票期权？。"
}
```

说明：

- `summary` 是会话级摘要。
- Streamlit 用户问答页会用该接口显示当前会话摘要。
- 如果 conversation 不存在，返回 `404`。

### POST /api/v1/conversations/{conversation_id}/messages

向某个会话新增一条消息。

请求示例：

```text
POST /api/v1/conversations/1/messages
```

请求体：

```json
{
  "role": "user",
  "content": "我叫陈晨"
}
```

成功返回：

```json
{
  "id": 1,
  "conversation_id": 1,
  "role": "user",
  "content": "我叫陈晨"
}
```

说明：

- `role` 可以表示消息角色，例如 `user` 或 `assistant`。
- `content` 是消息正文。
- 新增消息前会先检查 conversation 是否存在。
- 如果 conversation 不存在，返回 `404`。

错误示例：

```json
{
  "detail": "会话不存在。"
}
```

### GET /api/v1/conversations/{conversation_id}/messages

查看某个会话下的消息列表。

请求示例：

```text
GET /api/v1/conversations/1/messages
```

返回示例：

```json
[
  {
    "id": 1,
    "conversation_id": 1,
    "role": "user",
    "content": "我叫陈晨"
  },
  {
    "id": 2,
    "conversation_id": 1,
    "role": "assistant",
    "content": "我记住了，你叫陈晨。"
  }
]
```

说明：

- 一个 conversation 可以有多条 messages。
- `conversation_id` 用来建立 conversation 和 messages 的一对多关系。
- 如果 conversation 不存在，返回 `404`。

## 反馈接口

### POST /api/v1/feedback

保存用户对回答的反馈。

请求示例：

```json
{
  "question": "新员工什么时候完成安全培训？",
  "answer": "新员工需要在入职后30天内完成安全培训。",
  "rating": "helpful"
}

成功返回：

{
  "id": 1,
  "question": "新员工什么时候完成安全培训？",
  "answer": "新员工需要在入职后30天内完成安全培训。",
  "rating": "helpful"
}

### GET /api/v1/feedback

查看已保存的用户反馈列表。

返回示例：

```json
[
  {
    "id": 1,
    "question": "新员工什么时候完成安全培训？",
    "answer": "新员工需要在入职后30天内完成安全培训。",
    "rating": "helpful"
  }
]

### GET /api/v1/feedback/summary

查看用户反馈统计结果。

返回示例：

```json
{
  "total": 2,
  "helpful": 1,
  "not_helpful": 1
}

该接口可用于后续计算回答满意率，例如：helpful / total

### POST /api/v1/db/documents/with-content

新增 SQLite 文档，根据正文内容自动切分 chunks，并为 chunks 生成 embeddings。

请求示例：

```json
{
  "title": "远程办公制度",
  "file_type": "md",
  "content": "员工每周可以申请一天远程办公。远程办公需要提前提交申请。"
}
```

成功返回：

```json
{
  "id": 4,
  "title": "远程办公制度",
  "file_type": "md",
  "chunk_count": 2,
  "is_indexed": true
}
```

说明：

- `content` 会按句号、问号、感叹号和换行进行简单切分。
- 英文标点 `?` 和 `!` 也会被识别为切分边界。
- 空片段会被自动过滤。
- 超过最大长度的片段会继续按固定长度切分。
- `chunk_count` 由系统根据切分结果自动计算。
- `is_indexed` 根据是否成功生成 chunks 和 embeddings 自动设置。
- 新增时会调用 Ollama embedding 模型，默认使用 `bge-m3:latest`。
- 新增后可以立即通过 `/api/v1/db/chat/llm` 检索和问答。
- 文档标题默认最多 `100` 个字符。
- 文档正文默认最多 `20000` 个字符。

错误返回：

- `409 Conflict`：文档标题已存在
- `422 Unprocessable Entity`：文档标题过长，或文档正文没有有效内容，无法切分出 chunks
- `413 Payload Too Large`：文档正文过长，或上传文件过大
- `429 Too Many Requests`：请求过于频繁，请稍后再试
- `503 Service Unavailable`：文档索引失败，本地 Embedding 模型不可用

### Embedding 补索引

当历史 chunks 缺少 embeddings 时，可以运行：

```powershell
python -m week08.backfill_chunk_embeddings
```

## PostgreSQL 调试接口

> 说明：这组接口用于验证 PostgreSQL/pgvector 接入情况。当前主业务仍然默认使用 SQLite，PostgreSQL 接口暂时只作为学习和调试入口。

### GET /api/v1/postgresql/documents

从 PostgreSQL `documents` 表读取文档列表。

使用前需要确保：

- Docker Compose 中的 `postgres` 服务已经启动
- 当前后端进程使用 PostgreSQL 格式的 `DATABASE_URL`
- PostgreSQL schema 已经初始化

本地临时启动示例：

```powershell
docker compose up -d postgres
$env:DATABASE_URL="postgresql://agent_user:agent_password@localhost:5432/agent_db"
python -m uvicorn backend.main:app --reload
```

请求示例：

```text
GET /api/v1/postgresql/documents
```

返回示例：

```json
[
  {
    "id": 1,
    "title": "PostgreSQL 测试文档",
    "file_type": "md",
    "chunk_count": 0,
    "is_indexed": false
  },
  {
    "id": 2,
    "title": "PostgreSQL RAG 存储测试文档",
    "file_type": "md",
    "chunk_count": 1,
    "is_indexed": true
  }
]
```

如果当前 `DATABASE_URL` 仍然是 SQLite，会返回：

```text
400 Bad Request
```

说明：

- 该接口只读 PostgreSQL，不会修改数据。
- 该接口不会替代 `/api/v1/db/documents`。
- 当前 SQLite 文档接口仍然是主业务接口。

### GET /api/v1/postgresql/documents/{document_id}/chunks

从 PostgreSQL `chunks` 表读取某个文档的片段列表。

请求示例：

```text
GET /api/v1/postgresql/documents/2/chunks
```

返回示例：

```json
[
  {
    "id": 1,
    "document_id": 2,
    "text": "这是一条写入 PostgreSQL pgvector 的测试片段。"
  }
]
```

说明：

- 该接口只读 PostgreSQL，不会修改数据。
- 当前返回复用 `Chunk` 模型，所以只包含 `id`、`document_id` 和 `text`。
- PostgreSQL 表中的 `chunk_index` 暂时不会出现在接口返回里。
- 该接口不会替代 `/api/v1/db/documents/{document_id}/chunks`。

### POST /api/v1/postgresql/documents/with-content

把文档内容写入 PostgreSQL，并自动完成：

```text
正文内容 -> 切分 chunks -> Ollama bge-m3 生成 embedding -> 写入 pgvector
```

请求示例：

```json
{
  "title": "远程办公制度",
  "file_type": "md",
  "content": "员工每周可以申请一天远程办公。远程办公需要提前提交申请。"
}
```

成功返回：

```json
{
  "id": 1,
  "title": "远程办公制度",
  "file_type": "md",
  "chunk_count": 2,
  "is_indexed": true
}
```

状态码说明：

- `201 Created`：文档创建成功，并已写入 chunks 和 embeddings。
- `400 Bad Request`：当前 `DATABASE_URL` 不是 PostgreSQL URL。
- `409 Conflict`：文档创建失败，常见原因是标题重复或内容无法切出有效 chunks。
- `503 Service Unavailable`：Embedding 模型不可用，例如 Ollama 或 `bge-m3` 没有正常工作。

说明：

- 该接口会修改 PostgreSQL 数据。
- 重复运行相同标题会返回 `409`。
- 当前接口用于 PostgreSQL/pgvector 入库链路验收，还没有替代 SQLite 文档上传入口。
- 可用 `week10/postgresql_document_indexing_api_demo.py` 验证“入库后立刻自然语言检索”的完整闭环。

### DELETE /api/v1/postgresql/documents/{document_id}

按 ID 删除 PostgreSQL 文档。

请求示例：

```text
DELETE /api/v1/postgresql/documents/7
```

成功返回示例：

```json
{
  "message": "文档已删除。",
  "id": 7
}
```

状态码说明：

- `200 OK`：文档删除成功。
- `400 Bad Request`：当前 `DATABASE_URL` 不是 PostgreSQL URL。
- `404 Not Found`：指定 ID 的文档不存在。

说明：

- 该接口会修改 PostgreSQL 数据。
- 删除文档时，PostgreSQL 会通过外键级联删除该文档对应的 chunks 和 embeddings。
- 建议先通过 `GET /api/v1/postgresql/documents` 确认文档 ID，再执行删除。

### POST /api/v1/postgresql/search/vector

使用 PostgreSQL/pgvector 按向量相似度搜索 chunks。

请求示例：

```json
{
  "embedding": [1.0, 0.0, 0.0],
  "top_k": 2
}
```

注意：真实 PostgreSQL 表使用的是 `vector(1024)`，所以实际请求中的 `embedding` 需要是 1024 维。Swagger 页面不适合手动填写 1024 个数字，建议使用 demo 脚本验收：

```powershell
python -m week10.postgresql_vector_search_api_demo
```

返回示例：

```json
[
  {
    "chunk_id": 2,
    "document_id": 3,
    "document_title": "PostgreSQL 向量检索测试文档",
    "text": "员工每天需要完成 8 小时工作。",
    "distance": 0.0,
    "score": 1.0
  }
]
```

说明：

- 该接口是 PostgreSQL/pgvector 调试接口。
- 它要求调用方直接传入 embedding，不会自动把自然语言问题转换成向量。
- 最终自然语言问答接口后续会由后端调用 embedding 模型生成向量，再复用这类检索能力。
- 该接口不会替代当前 SQLite 问答接口。

### POST /api/v1/postgresql/search/question

使用自然语言问题搜索 PostgreSQL/pgvector 中的 chunks。

这个接口会在后端完成两步：

```text
用户问题 -> Ollama bge-m3 生成 embedding -> PostgreSQL pgvector 相似度检索
```

请求示例：

```json
{
  "question": "员工每天需要工作多久？",
  "top_k": 2
}
```

返回示例：

```json
{
  "question": "员工每天需要工作多久？",
  "embedding_size": 1024,
  "results": [
    {
      "chunk_id": 2,
      "document_id": 3,
      "document_title": "PostgreSQL 向量检索测试文档",
      "text": "员工每天需要完成 8 小时工作。",
      "distance": 0.1337358951568357,
      "score": 0.8662641048431643
    }
  ]
}
```

使用前需要确保：

- PostgreSQL 服务已经启动。
- 当前后端进程使用 PostgreSQL 格式的 `DATABASE_URL`。
- Ollama 已经启动，并且本地存在 `bge-m3:latest` embedding 模型。
- PostgreSQL `chunk_embeddings` 表中已经写入真实 embedding。

如果之前写入过 demo fake embedding，需要先运行真实 embedding 回填脚本：

```powershell
python -m week10.backfill_postgresql_chunk_embeddings
```

说明：

- `/search/vector` 适合调试“手动传 embedding”的底层 pgvector 检索能力。
- `/search/question` 适合调试“自然语言问题 -> embedding -> pgvector 检索”的完整检索链路。
- 当前接口仍然是 PostgreSQL 调试接口，还没有替代 SQLite/LangGraph Agent 主业务链路。
## PostgreSQL Retriever 接入 LangGraph Agent

`POST /api/v1/langgraph-agent/chat` 和 `POST /api/v1/langgraph-agent/conversations/{conversation_id}/chat` 现在支持通过查询参数切换检索后端：

```text
retriever_backend=postgresql
```

这个模式会走：

```text
用户问题 -> Ollama bge-m3 embedding -> PostgreSQL pgvector 检索 -> LangGraph Agent 校验上下文 -> 生成带引用回答
```

使用前需要确认：

- Docker Compose 中的 `postgres` 服务已经启动。
- 当前后端进程使用 PostgreSQL 格式的 `DATABASE_URL`。
- PostgreSQL schema 已初始化。
- PostgreSQL `chunk_embeddings` 表中已经写入真实 embedding。
- 本地 Ollama 已启动，并且存在 `bge-m3:latest` embedding 模型。

请求示例：

```text
POST /api/v1/langgraph-agent/chat?retriever_backend=postgresql&top_k=2&mode=precomputed_embedding&min_score=0.6&timeout_seconds=30
```

带会话保存的请求示例：

```text
POST /api/v1/langgraph-agent/conversations/1/chat?retriever_backend=postgresql&top_k=2&mode=precomputed_embedding&min_score=0.6&timeout_seconds=30
```

请求体：

```json
{
  "question": "员工每天需要工作多久？"
}
```

成功返回中应重点检查：

```json
{
  "retriever_backend": "postgresql",
  "has_valid_context": true,
  "citations": [
    {
      "path": "postgresql://chunk/2"
    }
  ]
}
```

说明：

- PostgreSQL retriever 返回的引用路径使用 `postgresql://chunk/{chunk_id}`。
- 对于 PostgreSQL / pgvector 检索，`validate_context_node` 不只依赖关键词包含判断；当检索片段相似度分数足够高时，也可以判定为有效上下文。
- 无会话版本和带会话保存版本都支持 `retriever_backend=postgresql`。
- 带会话保存版本会使用 PostgreSQL 做知识库检索，同时继续把 user/assistant 消息保存到 SQLite。
- `POST /api/v1/langgraph-agent/chat/stream` 目前仍保护性禁用 PostgreSQL retriever，后续再逐步接入。

## PostgreSQL evaluation 数据管理接口

PostgreSQL 文档表支持用 `source` 区分正式数据和评测数据：

```text
production  正式/默认数据
evaluation  评测验收数据
```

### GET /api/v1/postgresql/documents?source=evaluation

按来源过滤 PostgreSQL 文档列表。

示例：

```text
GET /api/v1/postgresql/documents?source=evaluation
GET /api/v1/postgresql/documents?source=production
```

说明：

- 不传 `source` 时返回全部 PostgreSQL 文档。
- 传 `source=evaluation` 时只返回评测文档。
- 传 `source=production` 时只返回正式/默认文档。

### GET /api/v1/postgresql/documents/evaluation/cleanup-preview

预览清理 `evaluation` 数据会影响多少内容。

返回示例：

```json
{
  "source": "evaluation",
  "document_count": 1,
  "chunk_count": 2,
  "embedding_count": 2,
  "documents": [
    {
      "id": 6,
      "title": "PostgreSQL Agent 端到端验收文档"
    }
  ]
}
```

说明：

- 该接口只读，不会删除数据。
- 适合在执行清理前确认影响范围。

### DELETE /api/v1/postgresql/documents/evaluation?confirm=true

清理 `source=evaluation` 的 PostgreSQL 评测文档。

示例：

```text
DELETE /api/v1/postgresql/documents/evaluation?confirm=true
```

返回示例：

```json
{
  "message": "评测文档已清理。",
  "deleted_count": 1
}
```

说明：

- 必须显式传入 `confirm=true`，否则返回 `400`。
- 该接口只清理 `source=evaluation` 的文档。
- `source=production` 的正式文档不会被清理。
