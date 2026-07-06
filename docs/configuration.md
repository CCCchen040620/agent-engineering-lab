# 配置说明

本项目的运行配置集中在 `backend/config.py` 中，并支持通过环境变量覆盖默认值。

## 配置项

| 环境变量 | 默认值 | 说明 |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama 服务地址 |
| `LLM_MODEL` | `qwen3.6:latest` | 本地大模型名称，用于生成回答 |
| `EMBEDDING_MODEL` | `bge-m3:latest` | Embedding 模型名称，用于生成语义向量 |
| `DEFAULT_TOP_K` | `3` | 默认最多返回的检索片段数量 |
| `DEFAULT_MIN_SCORE` | `0.3` | 默认最低相似度门槛 |

## PowerShell 示例

临时设置环境变量：

```powershell
$env:LLM_MODEL="qwen3.6:latest"
$env:EMBEDDING_MODEL="bge-m3:latest"
$env:DEFAULT_TOP_K="3"
$env:DEFAULT_MIN_SCORE="0.8"