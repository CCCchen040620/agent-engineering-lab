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

### 文档接口

- `GET /api/v1/documents`：查看文档列表
- `GET /api/v1/documents?indexed_only=true`：只查看已索引文档
- `GET /api/v1/documents?file_type=pdf`：按文件类型筛选
- `GET /api/v1/documents/by-id/{document_id}`：按 id 查看文档
- `POST /api/v1/documents`：新增文档
- `DELETE /api/v1/documents/by-id/{document_id}`：按 id 删除文档

## SQLite 文档接口

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

## SQLite 问答接口

### POST /api/v1/db/chat

从 SQLite `chunks` 表检索文档片段，并生成带引用来源的回答。

请求示例：

```json
{
  "question": "新员工什么时候完成安全培训？"
}

支持查询参数：

- `top_k`：最多返回几个引用片段，默认 `3`，范围 `1` 到 `5`

示例：

```text
POST /api/v1/db/chat?top_k=2
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