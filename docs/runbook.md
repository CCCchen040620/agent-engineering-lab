# 项目运行手册

本手册用于记录企业知识库 Agent 项目的常用启动和维护命令。

## 1. 检查测试

```powershell
pytest
```

当前稳定状态：

```text
217 passed
```

## 2. 启动 FastAPI 后端

```powershell
python -m uvicorn backend.main:app --reload
```

接口文档：

```text
http://127.0.0.1:8000/docs
```

健康检查：

```text
http://127.0.0.1:8000/health
```

## 3. 启动 Streamlit 用户问答页

```powershell
python -m streamlit run frontend/streamlit_app.py
```

主要功能：

- 新增知识文档
- RAG 问答
- 查看引用来源
- 提交回答反馈

## 4. 启动反馈管理页

```powershell
python -m streamlit run frontend/admin_feedback.py
```

主要功能：

- 查看反馈总数
- 查看有帮助 / 没帮助数量
- 查看反馈列表

## 5. 启动文档管理页

```powershell
python -m streamlit run frontend/admin_documents.py
```

主要功能：

- 查看文档列表
- 查看文档 chunks
- 查看 embedding 索引状态
- 补齐缺失 embeddings

## 6. 检查本地 Ollama 模型

```powershell
ollama list
```

当前项目使用：

```text
qwen3.6:latest  用于生成回答
bge-m3:latest   用于生成 embeddings
```

## 7. 补齐历史 chunk embeddings

```powershell
python -m week08.backfill_chunk_embeddings
```

该脚本会：

- 扫描 SQLite 中所有 chunks
- 跳过已经有 embedding 的 chunks
- 为缺失 chunks 调用 `bge-m3` 生成 embeddings
- 保存到 `chunk_embeddings` 表

该脚本可以重复运行。

## 8. 运行 LLM RAG 评测

默认配置：

```powershell
python -m week07.evaluate_llm_rag
```

指定检索模式和最低分数：

```powershell
python -m week07.evaluate_llm_rag embedding 0.8
```

报告保存位置：

```text
docs/evaluations/llm-rag-run.md
```

## 9. 比较检索模式

默认问题：

```powershell
python -m week08.compare_retrieval_modes
```

指定问题和最低分数：

```powershell
python -m week08.compare_retrieval_modes "员工可以远程办公吗？" 0.8
```

支持对比：

- `keyword`
- `vector`
- `embedding`
- `precomputed_embedding`

## 10. 配置环境变量

配置说明见：

```text
docs/configuration.md
```

PowerShell 示例：

```powershell
$env:DEFAULT_MIN_SCORE="0.8"
python -m streamlit run frontend/streamlit_app.py
```
