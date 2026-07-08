# 项目运行手册

本手册用于记录企业知识库 Agent 项目的常用启动和维护命令。

## 1. 检查测试

```powershell
pytest
```

当前稳定状态：

```text
282 passed, 1 warning
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

## 4. 调用 Agent API

启动 FastAPI 后端后，可以在接口文档中测试：

```text
http://127.0.0.1:8000/docs
```

接口路径：

```text
POST /api/v1/agent/chat
```

该接口是第一版手写 Simple Agent，当前支持：

- 文档列表
- 读取指定文档片段
- 知识库问答
- 无证据拒答
- 缺少文档标题时澄清

项目也提供了 LangGraph 版本 Agent 接口：

```text
POST /api/v1/langgraph-agent/chat
```

该接口用于安全迁移和对照测试。它当前支持：

- 文档列表
- 知识库问答
- 无证据拒答

目前读取指定文档片段仍然使用：

```text
POST /api/v1/agent/chat
```

两个接口的区别：

| 接口 | 内部实现 | 当前用途 |
|---|---|---|
| `/api/v1/agent/chat` | 普通 Python 手写流程 | 稳定版 Simple Agent |
| `/api/v1/langgraph-agent/chat` | LangGraph 状态图 | 新版 Agent 编排验证 |

请求示例：

```json
{
  "question": "新员工什么时候完成安全培训？"
}
```

也可以测试文档列表类问题：

```json
{
  "question": "知识库里有哪些文档？"
}
```

也可以测试读取文档类问题：

```json
{
  "question": "查看员工手册的片段"
}
```

如果问题缺少文档标题，Agent 会要求用户补充信息：

```json
{
  "question": "查看这份文档的片段"
}
```

该接口会返回：

- Agent 最终回答
- 引用来源
- 检索关键词
- Agent 执行步骤 `steps`

`steps` 字段用于观察 Agent 的执行过程，例如：

- 先调用 `decide_agent_intent` 判断用户意图
- 文档列表类问题调用 `list_documents_tool`
- 读取文档类问题调用 `find_document_by_title_tool` 和 `read_document_chunks_tool`
- 读取文档类问题缺少标题时调用 `ask_clarification_tool`
- 普通业务问题调用 `search_knowledge_base_tool`
- 根据检索结果继续调用 `answer_with_context_tool` 或 `refuse_answer_tool`

LangGraph Agent 的执行步骤也会放在 `steps` 字段中。区别是它的流程由 LangGraph 的节点和条件边管理：

- `decide_intent_node` 判断意图
- `list_documents_node` 处理文档列表问题
- `search_knowledge_node` 检索知识库
- `validate_context_node` 判断检索片段是否真的包含有效上下文
- `route_by_context` 根据 `has_valid_context` 分流
- `answer_node` 在上下文有效时回答
- `refuse_node` 在上下文无效时拒答

例如，用户问：

```text
公司有没有股票期权？
```

即使 embedding 检索命中了 3 个片段，只要这些片段不包含有效上下文，LangGraph Agent 仍然应该拒答。此时执行步骤应该类似：

```text
[1] decide_agent_intent -> route_by_intent
[2] search_knowledge_base_tool -> validate_context
[3] validate_context_node -> refuse_node
[4] refuse_answer_tool -> finish
```

## 5. 启动 Streamlit 用户问答页

```powershell
python -m streamlit run frontend/streamlit_app.py
```

主要功能：

- 新增知识文档
- RAG 问答
- 查看引用来源
- 提交回答反馈

## 6. 启动反馈管理页

```powershell
python -m streamlit run frontend/admin_feedback.py
```

主要功能：

- 查看反馈总数
- 查看有帮助 / 没帮助数量
- 查看反馈列表

## 7. 启动文档管理页

```powershell
python -m streamlit run frontend/admin_documents.py
```

主要功能：

- 查看文档列表
- 查看文档 chunks
- 查看 embedding 索引状态
- 补齐缺失 embeddings

## 8. 检查本地 Ollama 模型

```powershell
ollama list
```

当前项目使用：

```text
qwen3.6:latest  用于生成回答
bge-m3:latest   用于生成 embeddings
```

## 9. 补齐历史 chunk embeddings

```powershell
python -m week08.backfill_chunk_embeddings
```

该脚本会：

- 扫描 SQLite 中所有 chunks
- 跳过已经有 embedding 的 chunks
- 为缺失 chunks 调用 `bge-m3` 生成 embeddings
- 保存到 `chunk_embeddings` 表

该脚本可以重复运行。

## 10. 运行 LLM RAG 评测

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

## 11. 比较检索模式

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

## 12. 配置环境变量

配置说明见：

```text
docs/configuration.md
```

PowerShell 示例：

```powershell
$env:DEFAULT_MIN_SCORE="0.8"
python -m streamlit run frontend/streamlit_app.py
```

## 13. 后端旧进程排查

在 Windows 上使用 `uvicorn --reload` 时，偶尔会出现旧的父子进程没有完全退出，导致代码已经修改，但 API 仍然返回旧逻辑。

典型现象：

- 直接调用 Python 函数是新逻辑
- 但浏览器 `/docs` 或 Streamlit 页面仍然显示旧步骤
- 例如代码中已经有 `validate_context_node`，但 API 返回的 `steps` 里没有这一项

先检查 8000 端口：

```powershell
Get-NetTCPConnection -LocalPort 8000 -State Listen | Select-Object LocalAddress,LocalPort,OwningProcess
```

查看占用端口的进程：

```powershell
Get-CimInstance Win32_Process -Filter "ProcessId = 进程ID" | Select-Object ProcessId,Name,CommandLine
```

如果确认是本项目的旧 FastAPI 后端，可以停止它：

```powershell
Stop-Process -Id 进程ID
```

确认 8000 端口没有监听后，再用不带 `--reload` 的方式干净启动一次验证：

```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

验证正常后，再根据需要恢复使用：

```powershell
python -m uvicorn backend.main:app --reload
```
