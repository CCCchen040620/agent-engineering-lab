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
3. 如果是普通问答，则调用 `search_knowledge_base_tool`
4. 如果普通问答检索到片段，则调用 `answer_with_context_tool`
5. 如果普通问答没有检索到片段，则调用 `refuse_answer_tool`
6. 返回回答、引用来源和执行步骤

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

说明：

- 这是项目中的第一版 Agent 流程。
- 当前支持两类意图：`list_documents` 和 `answer_question`。
- 当前还没有使用 LangGraph，而是用普通 Python 函数手写决策流程。
- `steps` 字段用于展示 Agent 的执行过程，包括工具名、工具输入、观察结果和下一步动作。
- 当前支持的文档列表类问法包括：“知识库里有哪些文档？”、“请列出文档”、“查看文档列表”。
- 后续可以把这个流程迁移到 LangGraph 状态图。

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

错误返回：

- `409 Conflict`：文档标题已存在
- `422 Unprocessable Entity`：文档正文没有有效内容，无法切分出 chunks

### Embedding 补索引

当历史 chunks 缺少 embeddings 时，可以运行：

```powershell
python -m week08.backfill_chunk_embeddings
