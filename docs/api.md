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

异常降级说明：

当本地 Ollama/Qwen 服务不可用、超时或生成失败时，接口不会直接崩溃，而是返回友好提示：

```json
{
  "answer": "本地模型暂时不可用，请稍后再试。"
}

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

新增 SQLite 文档，并根据正文内容自动切分 chunks。

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
- `is_indexed` 根据是否成功生成 chunks 自动设置。
- 新增后可以立即通过 `/api/v1/db/chat/llm` 检索和问答。

错误返回：

- `409 Conflict`：文档标题已存在
- `422 Unprocessable Entity`：文档正文没有有效内容，无法切分出 chunks