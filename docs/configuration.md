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
- 当前项目不会自动读取 `.env` 文件；如果需要覆盖配置，可以在 PowerShell 中临时设置环境变量，或后续接入 dotenv 工具。

## 配置项

| 环境变量 | 默认值 | 说明 |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama 服务地址 |
| `BACKEND_API_BASE_URL` | `http://127.0.0.1:8000` | FastAPI 后端服务地址，Streamlit 上传 txt 文档时会调用这个地址 |
| `LLM_MODEL` | `qwen3.6:latest` | 本地大模型名称，用于生成回答 |
| `EMBEDDING_MODEL` | `bge-m3:latest` | Embedding 模型名称，用于生成语义向量 |
| `DEFAULT_TOP_K` | `3` | 默认最多返回的检索片段数量 |
| `DEFAULT_MIN_SCORE` | `0.3` | 默认最低相似度门槛 |

## PowerShell 示例

临时设置环境变量：

```powershell
$env:BACKEND_API_BASE_URL="http://127.0.0.1:8000"
$env:LLM_MODEL="qwen3.6:latest"
$env:EMBEDDING_MODEL="bge-m3:latest"
$env:DEFAULT_TOP_K="3"
$env:DEFAULT_MIN_SCORE="0.8"
