# 项目运行手册

本手册用于记录企业知识库 Agent 项目的常用启动和维护命令。

## 1. 检查测试

```powershell
pytest
```

当前稳定状态：

```text
236 passed
```

## 2. 推荐启动脚本

项目提供了 PowerShell 启动脚本，建议优先使用脚本，减少手动输入长命令。

启动 FastAPI 后端：

```powershell
.\scripts\start_backend.ps1
```

如果 PowerShell 提示不允许运行脚本，可以使用临时执行方式：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_backend.ps1
```

启动 Streamlit 用户问答页：

```powershell
.\scripts\start_frontend.ps1
```

启动文档管理页：

```powershell
.\scripts\start_admin_documents.ps1
```

启动反馈管理页：

```powershell
.\scripts\start_admin_feedback.ps1
```

推荐顺序：

1. 先确认 Ollama 已启动。
2. 启动 FastAPI 后端。
3. 另开一个 PowerShell 窗口启动 Streamlit 用户页面。
4. 需要管理数据时，再启动文档管理页或反馈管理页。

## 3. 启动 FastAPI 后端

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

## 4. 启动 Streamlit 用户问答页

```powershell
python -m streamlit run frontend/streamlit_app.py
```

主要功能：

- 新增知识文档
- RAG 问答
- 查看引用来源
- 提交回答反馈

## 5. 启动反馈管理页

```powershell
python -m streamlit run frontend/admin_feedback.py
```

主要功能：

- 查看反馈总数
- 查看有帮助 / 没帮助数量
- 查看反馈列表

## 6. 启动文档管理页

```powershell
python -m streamlit run frontend/admin_documents.py
```

主要功能：

- 查看文档列表
- 查看文档 chunks
- 查看 embedding 索引状态
- 补齐缺失 embeddings

## 7. 检查本地 Ollama 模型

```powershell
ollama list
```

当前项目使用：

```text
qwen3.6:latest  用于生成回答
bge-m3:latest   用于生成 embeddings
```

## 8. 补齐历史 chunk embeddings

```powershell
python -m week08.backfill_chunk_embeddings
```

该脚本会：

- 扫描 SQLite 中所有 chunks
- 跳过已经有 embedding 的 chunks
- 为缺失 chunks 调用 `bge-m3` 生成 embeddings
- 保存到 `chunk_embeddings` 表

该脚本可以重复运行。

## 9. 运行 LLM RAG 评测

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

## 10. 比较检索模式

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

## 11. 配置环境变量

配置说明见：

```text
docs/configuration.md
```

PowerShell 示例：

```powershell
$env:DEFAULT_MIN_SCORE="0.8"
python -m streamlit run frontend/streamlit_app.py
```
