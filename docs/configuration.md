# 配置说明

本项目的运行配置集中在 `backend/config.py` 中，并支持通过环境变量覆盖默认值。

项目提供了 [.env.example](../.env.example) 作为配置模板。

可以复制一份本地配置：

```powershell
Copy-Item .env.example .env
```

说明：

- `.env.example` 可以提交到 Git，用于说明需要哪些配置项。
- `.env` 是本地私有配置，已被 `.gitignore` 忽略，不应该提交。
- 当前项目启动时会自动读取 `.env` 文件；也可以在 PowerShell 中临时设置环境变量覆盖配置。

## 配置项

| 环境变量 | 默认值 | 说明 |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama 服务地址 |
| `BACKEND_API_BASE_URL` | `http://127.0.0.1:8000` | FastAPI 后端服务地址，Streamlit 上传 txt 文档时会调用这个地址 |
| `DATABASE_URL` | `sqlite:///data/app.db` | 数据库连接地址；当前默认使用 SQLite，后续迁移 PostgreSQL 时会改为 PostgreSQL 地址 |
| `LLM_MODEL` | `qwen3.6:latest` | 本地大模型名称，用于生成回答 |
| `EMBEDDING_MODEL` | `bge-m3:latest` | Embedding 模型名称，用于生成语义向量 |
| `DEFAULT_TOP_K` | `3` | 默认最多返回的检索片段数量 |
| `DEFAULT_MIN_SCORE` | `0.3` | 默认最低相似度门槛 |
| `MAX_DOCUMENT_TITLE_CHARS` | `100` | 文档标题最大字符数 |
| `MAX_DOCUMENT_CONTENT_CHARS` | `20000` | 手动新增文档正文最大字符数 |
| `MAX_UPLOAD_FILE_BYTES` | `1048576` | txt 上传文件最大字节数，默认约 1MB |
| `RATE_LIMIT_WINDOW_SECONDS` | `60` | 基础内存限流窗口秒数 |
| `RATE_LIMIT_MAX_REQUESTS` | `20` | 每个重型接口在限流窗口内允许的最大请求数 |
| `SLOW_REQUEST_THRESHOLD_MS` | `1000` | 慢请求日志阈值，单位毫秒 |

## PowerShell 示例

临时设置环境变量：

```powershell
$env:BACKEND_API_BASE_URL="http://127.0.0.1:8000"
$env:DATABASE_URL="sqlite:///data/app.db"
$env:LLM_MODEL="qwen3.6:latest"
$env:EMBEDDING_MODEL="bge-m3:latest"
$env:DEFAULT_TOP_K="3"
$env:DEFAULT_MIN_SCORE="0.8"
$env:MAX_DOCUMENT_TITLE_CHARS="100"
$env:MAX_DOCUMENT_CONTENT_CHARS="20000"
$env:MAX_UPLOAD_FILE_BYTES="1048576"
$env:RATE_LIMIT_WINDOW_SECONDS="60"
$env:RATE_LIMIT_MAX_REQUESTS="20"
$env:SLOW_REQUEST_THRESHOLD_MS="1000"
```

## DATABASE_URL 说明

当前 SQLite 默认地址：

```text
sqlite:///data/app.db
```

其中：

- `sqlite` 表示数据库类型是 SQLite。
- `data/app.db` 表示本地数据库文件路径。

后续迁移 PostgreSQL 时，地址会变成类似：

```text
postgresql://agent_user:password@localhost:5432/agent_db
```

这一步目前只是把数据库地址配置化，并增加 URL 解析能力；项目主流程仍然使用 SQLite。

代码中的 `DATABASE_PATH` 不是单独的环境变量，而是从 `DATABASE_URL` 推导出来的内部配置。

例如：

```text
DATABASE_URL=sqlite:///data/app.db
DATABASE_PATH=data/app.db
```

后续旧 SQLite 代码会逐步从 `DATABASE_PATH` 读取数据库文件路径，而不是继续直接依赖写死路径。
