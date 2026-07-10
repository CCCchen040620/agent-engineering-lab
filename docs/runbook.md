# 项目运行手册

本手册用于记录企业知识库 Agent 项目的常用启动和维护命令。

## 1. 检查测试

```powershell
pytest
```

也可以运行本地健康检查脚本：

```powershell
.\scripts\check_project.ps1
```

当前稳定状态：

```text
360 passed, 1 warning
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

迁移 SQLite schema：

```powershell
.\scripts\migrate_sqlite.ps1
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
2. 运行 SQLite schema 迁移脚本。
3. 启动 FastAPI 后端。
4. 另开一个 PowerShell 窗口启动 Streamlit 用户页面。
5. 需要管理数据时，再启动文档管理页或反馈管理页。

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
- 读取指定文档片段
- 知识库问答
- 无证据拒答

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
- `extract_document_title_node` 提取读取文档类问题中的文档标题
- `find_document_node` 根据标题查找文档
- `read_document_chunks_node` 读取文档 chunks 并生成引用
- `ask_clarification_node` 在缺少文档标题时要求用户补充信息
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

读取文档类问题可以测试：

```text
查看员工手册的片段
```

预期执行步骤类似：

```text
[1] decide_agent_intent -> route_by_intent
[2] extract_document_title -> find_document_node
[3] find_document_by_title_tool -> read_document_chunks_node
[4] read_document_chunks_tool -> finish
```

缺少文档标题时可以测试：

```text
查看这份文档的片段
```

预期执行步骤类似：

```text
[1] decide_agent_intent -> route_by_intent
[2] extract_document_title -> ask_clarification_node
[3] ask_clarification_tool -> finish
```

## 5. 启动 Streamlit 用户问答页

```powershell
python -m streamlit run frontend/streamlit_app.py
```

主要功能：

- 新增知识文档
- RAG 问答
- Simple Agent 问答
- LangGraph Agent 问答
- 保存 LangGraph Agent 本轮问答到会话
- 显示当前会话摘要
- 查看引用来源
- 查看 Agent 执行步骤
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

## 9. 迁移 SQLite schema

当代码新增了数据库字段，而本地 `data/app.db` 是旧版本时，需要先运行迁移脚本。

例如本项目新增 conversation 的 `summary` 字段或 message 的 `metadata_json` 字段后，旧数据库如果没有这些字段，带会话存储的 LangGraph Agent 可能会在读取会话或保存消息时报错。

运行：

```powershell
python -m week10.migrate_sqlite_schema
```

该脚本会：

- 创建缺失的 `conversations` 表
- 创建缺失的 `messages` 表
- 检查 `conversations.summary` 是否存在
- 如果缺少 `summary`，自动添加
- 检查 `messages.metadata_json` 是否存在
- 如果缺少 `metadata_json`，自动添加
- 如果已经存在，直接跳过

运行后会输出迁移结果，例如：

```text
SQLite schema migration completed.
{'conversations_table_ready': True, 'messages_table_ready': True, 'summary_added': False, 'metadata_json_added': False}
```

其中：

- `summary_added=True` 表示本次真的新增了会话摘要字段
- `metadata_json_added=True` 表示本次真的新增了字段
- `metadata_json_added=False` 表示字段已经存在，本次安全跳过

该脚本可以重复运行。

## 10. 补齐历史 chunk embeddings

```powershell
python -m week08.backfill_chunk_embeddings
```

该脚本会：

- 扫描 SQLite 中所有 chunks
- 跳过已经有 embedding 的 chunks
- 为缺失 chunks 调用 `bge-m3` 生成 embeddings
- 保存到 `chunk_embeddings` 表

该脚本可以重复运行。

## 11. 补齐历史 conversation summaries

```powershell
python -m week10.backfill_conversation_summaries
```

该脚本会：

- 扫描 SQLite 中所有 conversations
- 跳过已经有 summary 的会话
- 根据旧 messages 生成 summary
- 写回 `conversations.summary`

该脚本可以重复运行。

注意：

- migration 负责补表结构。
- backfill 负责补历史数据。

## 12. 运行 LLM RAG 评测

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

## 13. 比较检索模式

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

## 14. 配置环境变量

配置说明见：

```text
docs/configuration.md
```

PowerShell 示例：

```powershell
$env:DEFAULT_MIN_SCORE="0.8"
python -m streamlit run frontend/streamlit_app.py
```

## 15. 测试 LangGraph Memory Demo API

启动 FastAPI 后端后，可以在 `/docs` 中测试：

```text
POST /api/v1/memory-demo/chat?thread_id=chen
```

第一次请求：

```json
{
  "question": "我叫陈晨"
}
```

预期回答：

```text
我记住了，你叫陈晨。
```

第二次仍然使用同一个 `thread_id=chen`：

```json
{
  "question": "我叫什么？"
}
```

预期回答：

```text
你叫陈晨。
```

如果换成：

```text
thread_id=other
```

再问：

```json
{
  "question": "我叫什么？"
}
```

预期回答：

```text
我还不知道你的名字。
```

说明：

- `thread_id` 相当于会话 ID。
- 当前 demo 使用 `InMemorySaver`，只保存在内存中。
- 后端进程重启后，记忆会消失。
- 这个接口用于理解 LangGraph checkpoint，不是正式长期记忆方案。

## 16. 测试 Conversation API

Conversation API 用于保存会话和消息，是后续正式接入 LangGraph memory 的数据库基础。

启动 FastAPI 后端后，可以在 `/docs` 中测试。

### 16.1 创建会话

接口：

```text
POST /api/v1/conversations
```

请求：

```json
{
  "title": "第一次对话"
}
```

预期返回：

```json
{
  "id": 1,
  "title": "第一次对话",
  "summary": ""
}
```

### 16.2 查看会话列表

接口：

```text
GET /api/v1/conversations
```

预期返回会话列表：

```json
[
  {
    "id": 1,
    "title": "第一次对话",
    "summary": ""
  }
]
```

### 16.3 查看单个会话详情

接口：

```text
GET /api/v1/conversations/1
```

预期返回：

```json
{
  "id": 1,
  "title": "第一次对话",
  "summary": ""
}
```

说明：

- `summary` 是会话级摘要。
- Streamlit 用户问答页会用该接口显示当前会话摘要。

### 16.4 给会话新增消息

接口：

```text
POST /api/v1/conversations/1/messages
```

请求：

```json
{
  "role": "user",
  "content": "我叫陈晨"
}
```

也可以新增 assistant 消息：

```json
{
  "role": "assistant",
  "content": "我记住了，你叫陈晨。"
}
```

### 16.5 查看会话消息

接口：

```text
GET /api/v1/conversations/1/messages
```

预期返回：

```json
[
  {
    "id": 1,
    "conversation_id": 1,
    "role": "user",
    "content": "我叫陈晨"
  },
  {
    "id": 2,
    "conversation_id": 1,
    "role": "assistant",
    "content": "我记住了，你叫陈晨。"
  }
]
```

### 16.6 找不到会话时

如果请求：

```text
GET /api/v1/conversations/999/messages
```

预期返回：

```text
404
```

原因：

```text
找不到会话是一种可预期的业务结果，不是系统崩溃。
```

后续可以把：

```text
conversation_id
```

作为 LangGraph 的：

```text
thread_id
```

这样数据库中的长期会话历史和 LangGraph 的运行时 memory 就可以对齐。

## 17. 测试带会话存储的 LangGraph Agent

该接口用于把 LangGraph Agent 的本轮问答结果保存到 SQLite messages 表。

它不是 Memory Demo API。

区别：

| 接口 | 作用 | 是否重启后保留 |
|---|---|---|
| `/api/v1/memory-demo/chat?thread_id=...` | 演示 `InMemorySaver` 短期记忆 | 否 |
| `/api/v1/langgraph-agent/conversations/{conversation_id}/chat` | 调用真实 LangGraph Agent，并保存 user/assistant 消息 | 是 |

### 17.1 先创建会话

```text
POST /api/v1/conversations
```

请求：

```json
{
  "title": "LangGraph 会话测试"
}
```

记下返回的：

```text
id
```

### 17.2 调用带会话存储的 LangGraph Agent

假设会话 ID 是 `1`：

```text
POST /api/v1/langgraph-agent/conversations/1/chat
```

请求：

```json
{
  "question": "公司有没有股票期权？"
}
```

预期结果：

- 返回 LangGraph Agent 的回答
- 返回 `conversation_id`
- 返回更新后的 `conversation_summary`
- 返回 `saved_messages`
- `saved_messages` 中应该有两条：
  - `role=user`
  - `role=assistant`

### 17.3 查看消息是否入库

```text
GET /api/v1/conversations/1/messages
```

预期可以看到刚才保存的 user 和 assistant 消息。

### 17.4 在 Streamlit 页面中保存 LangGraph Agent 问答

这个流程用于验收前端页面是否正确接入带会话存储的 LangGraph Agent。

前置条件：

1. FastAPI 后端已启动。
2. Streamlit 用户问答页已启动。
3. 已经通过 `POST /api/v1/conversations` 创建会话，并拿到 `id`。

页面操作：

1. 在侧边栏选择 `LangGraph Agent 问答`。
2. 勾选 `保存 LangGraph Agent 问答到会话`。
3. 在 `conversation_id` 输入框里填写刚才创建的会话 ID。
4. 输入问题，例如：

```text
公司有没有股票期权？
```

预期页面显示：

```text
已保存到会话：1
本轮保存消息数：2
当前会话摘要：最近问题：公司有没有股票期权？。
```

然后再调用：

```text
GET /api/v1/conversations/1/messages
```

预期可以看到两条新消息：

- `role=user`
- `role=assistant`

如果填写的 `conversation_id` 不存在，前端会显示后端返回的错误信息：

```text
会话不存在。
```

说明：

- 该页面会把本轮 user/assistant 消息保存到 SQLite。
- 带会话存储的 LangGraph Agent 会读取同一 `conversation_id` 下的历史 messages 和 summary，做有限的上下文增强。
- 当前支持基于最近引用文档或 summary 构造 `contextual_question`，例如把“每天需要工作多久？”改写为“员工手册 每天需要工作多久？”。
- 当前会按最近引用文档过滤 snippets，减少无关引用混入。
- 如果当前问题和历史上下文不相关，Agent 应该拒答，避免上下文污染。
- summary 只用于辅助检索方向，不能直接作为最终回答依据。
- 这还不是完整长期记忆：目前没有用户画像、跨会话记忆，也没有把全部历史内容交给模型自由推理。

### 17.5 验收会话上下文检索增强

该验收用于确认“历史消息能辅助后续检索，但不会污染无关问题”。

前置条件：

1. 创建一个新的 conversation。
2. 调用带会话存储的 LangGraph Agent。
3. 查询参数建议使用：

```text
mode=vector
top_k=3
min_score=0
```

第一轮问题：

```json
{
  "question": "新员工什么时候完成安全培训？"
}
```

预期：回答引用 `员工手册`。

第二轮问题：

```json
{
  "question": "每天需要工作多久？"
}
```

预期：

- 回答包含 `8 小时`
- `steps` 中的 `search_knowledge_base_tool.input.contextual_question` 类似 `员工手册 每天需要工作多久？`
- `context_document_title` 为 `员工手册`
- `citations` 只保留 `员工手册` 相关片段

第三轮问题：

```json
{
  "question": "报销需要什么材料？"
}
```

预期：

- `has_valid_context` 为 `false`
- `citations` 为空列表
- 回答为拒答文案，不能强行使用 `员工手册` 回答报销问题

### 17.6 会话不存在时

如果请求：

```text
POST /api/v1/langgraph-agent/conversations/999/chat
```

预期返回：

```text
404
```

原因：

```text
不能把消息写入不存在的会话。
```

注意：

- 当前接口已经会读取历史 messages 做有限上下文增强。
- 它仍不是完整长期记忆方案。
- 后续可以继续引入摘要记忆、历史压缩、用户偏好记忆，以及更完整的 LangGraph checkpoint 持久化。

## 18. 后端旧进程排查

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
