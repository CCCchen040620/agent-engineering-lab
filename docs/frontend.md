# Streamlit 网页界面说明

本项目提供了一个基于 Streamlit 的网页界面，用于演示企业知识库 Agent 的 RAG 问答能力。

## 启动前准备

请先确认：

- SQLite 数据库 `data/app.db` 已存在
- Ollama 已启动
- 本地模型 `qwen3.6:latest` 可用

可以使用下面命令查看本地模型：

```powershell
ollama list