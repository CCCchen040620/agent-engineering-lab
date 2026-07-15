# 项目运行手册

## 任务中心当前验收

当前任务中心已经不只是早期的内存任务演示。以当前代码为准：

- 当 `DATABASE_URL` 使用 PostgreSQL 时，任务记录会保存到 PostgreSQL。
- 支持 PostgreSQL embedding 回填任务。
- 支持 PostgreSQL 文档异步入库任务。
- 任务列表默认最新任务优先。
- 失败任务会保存结构化错误原因，并在任务中心显示处理建议。
- 任务会显示轻量进度：`pending/running/succeeded/failed/canceled`。
- 失败任务支持异步重试，并记录 `retry_of_task_id`，方便追溯来源。
- 任务会记录 `run_count` 和 `retry_count`，用于观察运行次数和重试派生次数。
- 等待执行的 `pending` 任务支持取消。
- 当前仍然不是生产级队列系统：异步执行仍使用 FastAPI 进程内的轻量线程，还没有独立 worker、自动重试策略、运行中任务取消、并发控制和分布式队列。

交付前可以运行任务中心专项验收：

```powershell
.\scripts\check_task_center.ps1
```

运行前需要确认：

1. Docker Desktop 已启动。
2. PostgreSQL / pgvector 已启动：`docker compose up -d postgres`。
3. FastAPI 已用 PostgreSQL `DATABASE_URL` 启动。
4. Ollama 和 embedding 模型可用。

该脚本会创建一个 PostgreSQL 文档异步入库任务，轮询任务状态，并校验任务结果中包含 `document_id`、`chunk_count` 和 `embedding_count`。

## 后台任务中心

任务中心用于查看后台任务状态，并手动触发 PostgreSQL embedding 回填。

启动前请先确认 FastAPI 后端已经运行。如果要执行 PostgreSQL embedding 回填，请同时确认：

```powershell
docker compose up -d postgres
$env:DATABASE_URL="postgresql://agent_user:agent_password@localhost:5432/agent_db"
```

启动任务中心页面：

```powershell
python -m streamlit run frontend/admin_tasks.py
```

当前支持的操作：

- 查看任务列表
- 查看任务状态和错误信息
- 按状态筛选任务
- 按任务 ID 正序/倒序查看任务
- 限制任务列表最多显示数量
- 按任务 ID 查看单个任务详情
- 一键触发 PostgreSQL embedding 回填
- 选择同步或异步运行方式
- 查看任务结果摘要：`total_chunks`、`updated_embeddings`、`skipped_embeddings`、`model`
- 查看任务进度：`progress_percent` 和 `progress_message`
- 重试失败任务：基于旧任务的 `type` 和 `payload` 创建新任务，并记录 `retry_of_task_id`
- 查看任务统计：`run_count` 和 `retry_count`
- 取消等待任务：只允许取消尚未开始执行的 `pending` 任务

运行方式说明：

- `同步运行（等待完成）`：页面会等待任务执行结束，适合本地小规模验收。
- `异步运行（立即返回）`：页面会先创建任务，再调用异步运行接口，任务进入 `running` 后立即返回；后续刷新任务列表查看是否变成 `succeeded` 或 `failed`。

验收重点：

- 点击“运行 PostgreSQL embedding 回填”后，页面不应崩溃
- 同步运行成功时，页面会直接显示 `succeeded`
- 异步运行成功启动时，页面会先显示任务已开始；刷新任务列表后应能看到最终状态
- 如果 PostgreSQL、Ollama 或 embedding 模型不可用，任务状态应为 `failed`，并在 `error` 中记录原因
- 如果所有 chunks 已经有 embedding，结果中 `updated_embeddings` 可以为 `0`，`skipped_embeddings` 等于已有 embedding 的 chunks 数量
- 如果任务失败，可以输入失败任务 ID，点击“重试失败任务（异步）”，新任务应显示重试来源
- 如果任务仍是 `pending`，可以输入任务 ID，点击“取消等待任务”，状态应变为 `canceled`
- 如果任务已经 `running`，当前版本不会强行中断线程，取消接口会拒绝该请求

说明：当前任务中心仍是学习版任务流程。当后端使用 PostgreSQL `DATABASE_URL` 启动时，任务记录会保存到 PostgreSQL；异步执行仍使用 FastAPI 进程内的轻量后台线程。它已经支持轻量进度、失败任务重试和 pending 任务取消，但还不是生产级队列系统，暂不支持独立 worker、自动重试策略、运行中任务取消、并发控制和分布式队列。

SQLite Task Repository 保留为任务表结构学习样本；当前任务 API 优先走 PostgreSQL Task Repository。后续如果继续生产化，建议让 PostgreSQL 保存任务记录和审计数据，由 Redis / worker 负责排队、执行、重试、取消和进度。

本手册用于记录企业知识库 Agent 项目的常用启动和维护命令。

## 1. 检查测试

如果不确定当前应该跑哪个验收命令，先运行检查命令菜单：

```powershell
.\scripts\list_project_checks.ps1
```

该脚本只会按依赖范围列出常用检查命令，不会执行测试、启动服务或修改数据。

第一次拉取项目、换电脑、重装依赖或排查环境问题时，先运行开发环境自检：

```powershell
.\scripts\check_environment.ps1
```

该脚本会检查：

- Python、Git、pytest 是否可用
- Ollama、Docker 是否安装
- `.env.example`、`pyproject.toml`、`Dockerfile`、`docker-compose.yml` 是否存在
- 常用 PowerShell 脚本是否存在

说明：

- Python、Git、pytest 和关键项目文件是必需项。
- Ollama 和 Docker 是可选检查项；没有安装时会提示 warning，但不会阻止基础 Python 测试。
- 如果要使用本地大模型、embedding 或 Docker Compose，则需要单独确认 Ollama 和 Docker 可用。
- 项目最终目标栈是 Python 3.13；如果本机默认 `python` 不是 3.13，脚本会提示 warning。

日常回归测试：

```powershell
pytest
```

也可以运行本地项目检查脚本：

```powershell
.\scripts\check_project.ps1
```

该脚本会先迁移 SQLite schema，再运行完整测试。

## 运行统一 RAG 评测

当你想检查 RAG / Agent 的回答质量时，可以单独运行统一评测脚本：

```powershell
.\scripts\check_rag_evaluation.ps1
```

该脚本会读取：

```text
docs/evaluations/rag-cases.json
```

并生成：

```text
.local/evaluations/rag-evaluation-run.md
```

默认报告写入 `.local/evaluations/`，该目录不会提交到 Git，避免本地评测污染工作区。如果需要把某次报告作为正式记录，可以显式传入 `--report-path docs/evaluations/xxx.md`。

报告中的核心指标分为四层：

```text
业务通过率：问题类型、拒答、引用和期望文档是否符合业务预期
检索通过率：检索阶段是否找到了正确上下文，或无答案问题是否正确无召回
生成通过率：本地 LLM 是否成功生成回答，没有触发 fallback 或 timeout
端到端通过率：检索、生成、引用和最终回答整体是否严格通过
```

如果看到类似结果：

```text
业务通过率：1.0
检索通过率：1.0
生成通过率：0.8
端到端通过率：0.8
```

通常表示知识库检索链路是好的，问题主要出在本地模型生成稳定性上。

报告明细中还会显示：

```text
失败原因：fallback_answer
失败阶段：generation
兜底原因：HTTP Error 500: Internal Server Error
```

这类结果说明已经检索到相关资料，但 Ollama / LLM 生成回答时失败。当前项目会对 Ollama 生成调用自动重试一次；如果重试后仍失败，才会进入 fallback，并在报告里记录兜底原因。

注意：这个脚本是质量评测入口，不会替代普通测试。PostgreSQL 用例需要本机 PostgreSQL / pgvector 和 Ollama 环境可用；如果没有配置 PostgreSQL 连接，相关用例会被跳过。

如果只想运行一部分评测用例，可以直接使用 Python CLI 的通用筛选参数：

```powershell
.\.venv\Scripts\python.exe -m week11.run_rag_evaluation --scenario unknown_answer
```

```powershell
.\.venv\Scripts\python.exe -m week11.run_rag_evaluation --tag policy
```

```powershell
.\.venv\Scripts\python.exe -m week11.run_rag_evaluation --retriever-backend postgresql --tag unknown
```

这些参数只是按 `rag-cases.json` 里的通用字段筛选，不绑定具体业务含义。后续如果项目转成合同、客服或销售知识库，可以继续复用同一套 CLI。

查看系统依赖状态：

```text
GET /api/v1/system/status
```

该接口用于排查 API、SQLite、Ollama、LLM 模型和 Embedding 模型是否可用。

完整初始化项目可以运行：

```powershell
.\scripts\bootstrap_project.ps1
```

该脚本会依次执行：

1. 开发环境自检
2. SQLite schema migration
3. chunk embedding backfill
4. conversation summary backfill
5. pytest

如果只是临时想跳过环境自检，可以运行：

```powershell
.\scripts\bootstrap_project.ps1 -SkipEnvironmentCheck
```

如果暂时不想补齐 embedding，可以运行：

```powershell
.\scripts\bootstrap_project.ps1 -SkipEmbeddings
```

如果只想验证 bootstrap 前几步，不想运行完整测试，可以运行：

```powershell
.\scripts\bootstrap_project.ps1 -SkipTests
```

当前稳定状态：

```text
455 passed, 1 warning
```

GitHub Actions 当前包含两个检查：

- `test`：在 Windows + Python 3.13 环境运行 pytest。
- `docker-build`：在 Ubuntu 环境运行 `docker compose build`，验证 Dockerfile 和依赖配置可以构建镜像。

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

也可以使用 Docker Compose 启动后端和 Streamlit 前端：

先检查 Docker 镜像是否可以构建：

```powershell
.\scripts\check_docker_build.ps1
```

该脚本会执行 `docker compose build`，用于验证 Dockerfile 和 `pyproject.toml` 里的依赖配置是否能成功构建镜像。

构建通过后启动服务：

```powershell
docker compose up --build
```

访问地址：

```text
FastAPI: http://127.0.0.1:8000/docs
Streamlit: http://127.0.0.1:8501
```

Docker Compose 启动完成后，可以运行验收脚本：

```powershell
.\scripts\check_docker_compose.ps1
```

该脚本会检查 backend、frontend 容器是否运行，并检查 FastAPI 与 Streamlit 的健康接口是否可访问。

第一版 Docker Compose 不会把 Ollama 放进容器，而是默认访问宿主机：

```text
http://host.docker.internal:11434
```

因此使用 Docker Compose 前，仍然需要先确认本机 Ollama 已启动，并且模型可用：

```powershell
ollama list
```

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

## 4. 使用 Docker Compose 启动项目

第一版 Docker Compose 启动两个服务：

| 服务 | 端口 | 作用 |
|---|---|---|
| `backend` | `8000` | FastAPI 后端 |
| `frontend` | `8501` | Streamlit 用户问答页 |

启动：

```powershell
docker compose up --build
```

如果只想先验证镜像能不能构建，可以运行：

```powershell
.\scripts\check_docker_build.ps1
```

后台启动：

```powershell
docker compose up --build -d
```

停止：

```powershell
docker compose down
```

查看日志：

```powershell
docker compose logs -f
```

查看容器健康状态：

```powershell
docker compose ps
```

正常情况下，backend 和 frontend 都应该显示为 running 或 healthy。

启动完成后运行 Docker Compose 验收脚本：

```powershell
.\scripts\check_docker_compose.ps1
```

该脚本会检查：

- `backend` 服务是否 running
- `frontend` 服务是否 running
- `http://127.0.0.1:8000/health` 是否可访问
- `http://127.0.0.1:8501/_stcore/health` 是否可访问

如果脚本失败，优先检查 Docker Desktop 是否启动、容器是否仍在启动中、端口 8000/8501 是否被占用。

说明：

- backend 启动时会先运行 `python -m week10.migrate_sqlite_schema`。
- backend 会通过 `/health` 做健康检查。
- frontend 会通过 Streamlit 的 `/_stcore/health` 做健康检查。
- frontend 会等 backend 健康后再启动。
- 项目目录会挂载到容器 `/app`。
- SQLite 数据库仍然写在本地 `data/app.db`。
- Ollama 默认使用宿主机服务，不进入容器。
- 如果在 Docker 中无法访问 Ollama，请确认本机 Ollama 已启动。
- Docker Compose 默认用 `DOCKER_OLLAMA_BASE_URL` 覆盖容器内的 Ollama 地址。
- 如果看到 `failed to connect to the docker API`，通常表示 Docker Desktop 没有启动，先打开 Docker Desktop 后再重试。

示例：

```powershell
$env:DOCKER_OLLAMA_BASE_URL="http://host.docker.internal:11434"
docker compose up --build
```

## 5. 调用 Agent API

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

## 6. 启动 Streamlit 用户问答页

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

## 7. 启动反馈管理页

```powershell
python -m streamlit run frontend/admin_feedback.py
```

主要功能：

- 查看反馈总数
- 查看有帮助 / 没帮助数量
- 查看反馈列表

## 8. 启动文档管理页

```powershell
python -m streamlit run frontend/admin_documents.py
```

主要功能：

- 查看文档列表
- 查看文档 chunks
- 查看 embedding 索引状态
- 补齐缺失 embeddings

## 9. 检查本地 Ollama 模型

```powershell
ollama list
```

当前项目使用：

```text
qwen3.6:latest  用于生成回答
bge-m3:latest   用于生成 embeddings
```

## 10. 迁移 SQLite schema

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

迁移脚本默认使用 `DATABASE_URL` 推导出的 `DATABASE_PATH`，所以修改 `.env` 中的 `DATABASE_URL` 后，迁移目标也会随之变化。

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

## 11. 补齐历史 chunk embeddings

```powershell
python -m week08.backfill_chunk_embeddings
```

该脚本会：

- 扫描 SQLite 中所有 chunks
- 跳过已经有 embedding 的 chunks
- 为缺失 chunks 调用 `bge-m3` 生成 embeddings
- 保存到 `chunk_embeddings` 表

该脚本可以重复运行。

## 12. 补齐历史 conversation summaries

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

## 13. 运行 LLM RAG 评测

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

## 14. 比较检索模式

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

## 15. 配置环境变量

配置说明见：

```text
docs/configuration.md
```

PowerShell 示例：

```powershell
$env:DEFAULT_MIN_SCORE="0.8"
python -m streamlit run frontend/streamlit_app.py
```

### 15.1 基础内存限流

当前项目对部分重型接口启用了基础内存限流，默认每个客户端在 60 秒内最多请求 20 次。

受保护的接口包括：

- `POST /api/v1/db/chat/llm`
- `POST /api/v1/langgraph-agent/chat`
- `POST /api/v1/langgraph-agent/conversations/{conversation_id}/chat`
- `POST /api/v1/db/documents/with-content`
- `POST /api/v1/db/documents/upload-text`

超过限制时会返回：

```text
429 Too Many Requests
```

说明：

- 这是第一版本地内存限流。
- 后端重启后限流计数会清空。
- 触发限流时，后端会记录 `rate_limit_exceeded path=... client=... retry_after=...` 日志，方便排查是不是请求太频繁。
- 如果以后部署到多进程或多机器环境，可以升级为 Redis 或 API Gateway 限流。

## 16. 测试 LangGraph Memory Demo API

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

## 17. 测试 Conversation API

Conversation API 用于保存会话和消息，是后续正式接入 LangGraph memory 的数据库基础。

启动 FastAPI 后端后，可以在 `/docs` 中测试。

### 17.1 创建会话

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

### 17.2 查看会话列表

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

### 17.3 查看单个会话详情

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

### 17.4 给会话新增消息

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

### 17.5 查看会话消息

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

### 17.6 找不到会话时

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

## 18. 测试带会话存储的 LangGraph Agent

该接口用于把 LangGraph Agent 的本轮问答结果保存到 SQLite messages 表。

它不是 Memory Demo API。

区别：

| 接口 | 作用 | 是否重启后保留 |
|---|---|---|
| `/api/v1/memory-demo/chat?thread_id=...` | 演示 `InMemorySaver` 短期记忆 | 否 |
| `/api/v1/langgraph-agent/conversations/{conversation_id}/chat` | 调用真实 LangGraph Agent，并保存 user/assistant 消息 | 是 |

### 18.1 先创建会话

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

### 18.2 调用带会话存储的 LangGraph Agent

假设会话 ID 是 `1`：

```text
POST /api/v1/langgraph-agent/conversations/1/chat
```

如果要使用 PostgreSQL / pgvector 作为检索后端，可以追加查询参数：

```text
POST /api/v1/langgraph-agent/conversations/1/chat?retriever_backend=postgresql&mode=precomputed_embedding&top_k=3&min_score=0.6
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
- 如果使用 `retriever_backend=postgresql`，引用路径应类似 `postgresql://chunk/{chunk_id}`

### 18.3 查看消息是否入库

```text
GET /api/v1/conversations/1/messages
```

预期可以看到刚才保存的 user 和 assistant 消息。

### 18.4 在 Streamlit 页面中保存 LangGraph Agent 问答

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

### 18.5 验收会话上下文检索增强

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

### 18.6 会话不存在时

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

## 19. 后端日志

后端日志配置位于：

```text
backend/logging_config.py
```

FastAPI 启动时会初始化日志格式。

每次请求进入后端时，都会生成或复用一个 `request_id`，并写入响应头：

```text
X-Request-ID: ...
```

后端也会记录请求开始和结束日志：

```text
request_started method=... path=... request_id=...
```

```text
request_finished method=... path=... status_code=... request_id=... duration_ms=...
```

排查问题时，可以用同一个 `request_id` 把一次请求产生的多条日志串起来看。

如果请求耗时超过 `SLOW_REQUEST_THRESHOLD_MS`，后端会额外记录慢请求日志：

```text
slow_request method=... path=... request_id=... duration_ms=... threshold_ms=...
```

默认阈值是 1000ms，可以在 `.env` 中调整。

当前 LangGraph Agent 问答会记录两类关键日志：

```text
langgraph_agent_started question=... mode=... top_k=... min_score=...
```

```text
langgraph_agent_finished intent=... keyword=... has_valid_context=... citation_count=...
```

正常回答时，`has_valid_context` 通常为 `True`，`citation_count` 大于 0。

拒答时，`has_valid_context` 通常为 `False`，`citation_count` 为 0。

当前日志只输出到后端终端，暂时没有写入日志文件。

如果本地 LLM 生成失败，后端会记录 warning 日志：

```text
ollama_generation_failed model=...
```

如果本地 Embedding 生成失败，后端会记录 warning 日志：

```text
ollama_embedding_failed model=...
```

## 19.1 统一错误响应

后端错误响应会保留 `detail` 字段，同时增加统一的 `error` 和 `request_id` 字段。

示例：

```json
{
  "detail": "文档不存在。",
  "error": {
    "code": "not_found",
    "message": "文档不存在。",
    "status_code": 404
  },
  "request_id": "..."
}
```

这样做的好处是：旧代码仍然可以读取 `detail`，新前端可以统一读取 `error.message`，排查问题时可以用 `request_id` 对应后端日志。

## 20. 后端旧进程排查

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
## 检查 PostgreSQL 服务

启动 PostgreSQL：

```powershell
docker compose up -d postgres
```

查看服务状态：

```powershell
docker compose ps
```

预期结果：

- `postgres` 服务处于 `Up` 状态
- 状态中包含 `healthy`
- 端口映射包含 `5432->5432`

也可以运行项目脚本做快速检查：

```powershell
.\scripts\check_postgres.ps1
```

预期输出：

```text
PostgreSQL check completed successfully.
```

如果需要确认 pgvector 扩展已经可用，可以进入 PostgreSQL 后执行：

```sql
SELECT extname FROM pg_extension WHERE extname = 'vector';
```

预期结果中应该包含：

```text
vector
```

## 验证后端代码可以连接 PostgreSQL

这一步只是验证“后端代码能连上 PostgreSQL”，不代表主业务已经切换到 PostgreSQL。

先临时设置当前 PowerShell 窗口里的数据库地址：

```powershell
$env:DATABASE_URL="postgresql://agent_user:agent_password@localhost:5432/agent_db"
```

然后运行 PostgreSQL 状态检查：

```powershell
python -c "from backend.services.system_status_service import check_postgresql_status; print(check_postgresql_status())"
```

预期结果类似：

```text
{'enabled': True, 'status': 'ok', 'database_url': 'postgresql://agent_user:agent_password@localhost:5432/agent_db'}
```

重点看：

```text
'enabled': True
'status': 'ok'
```

验收完成后，恢复当前 PowerShell 窗口的环境变量：

```powershell
Remove-Item Env:DATABASE_URL
```

## 一键验收 PostgreSQL LangGraph Agent

当 PostgreSQL/pgvector、Ollama embedding、LangGraph Agent 都有改动时，可以运行专项验收脚本：

```powershell
.\scripts\check_postgresql_agent.ps1
```

该脚本会依次执行：

1. 检查 Docker Compose 中的 PostgreSQL 服务是否运行并健康。
2. 初始化 PostgreSQL 知识库表结构。
3. 回填 PostgreSQL chunk embeddings。
4. 运行 PostgreSQL 检索评测。
5. 运行 PostgreSQL LangGraph Agent 业务验收。
6. 写入一份端到端验收文档，并验证 Agent 能引用这份新文档回答。
7. 验证 `retriever_backend=postgresql` 可以和会话保存接口一起工作。

如果当前 PowerShell 窗口没有设置 `DATABASE_URL`，脚本会默认使用：

```text
postgresql://agent_user:agent_password@localhost:5432/agent_db
```

如果只是想跳过 embedding 回填，可以运行：

```powershell
.\scripts\check_postgresql_agent.ps1 -SkipEmbeddingBackfill
```

该脚本会优先使用项目虚拟环境中的 `.venv\Scripts\python.exe`。如果本机系统 Python 没有安装 `psycopg`，也不会影响该脚本运行。

注意：这个脚本是 PostgreSQL Agent 专项验收，不会替代普通的 `pytest` 或 `.\scripts\check_project.ps1`。

当前项目仍然默认保留 SQLite 作为学习版和会话/反馈存储。PostgreSQL/pgvector 已经可以作为实验性知识库检索后端，用于文档、chunks、embeddings 和 LangGraph Agent 检索。

## 初始化 PostgreSQL 知识库表结构

这一步会在 PostgreSQL 中创建知识库核心表：

- `documents`
- `chunks`
- `chunk_embeddings`

它只负责建表，不会把当前 SQLite 里的业务数据迁移过去。

先确认 PostgreSQL 已经启动：

```powershell
docker compose up -d postgres
```

临时设置当前 PowerShell 窗口的数据库地址：

```powershell
$env:DATABASE_URL="postgresql://agent_user:agent_password@localhost:5432/agent_db"
```

运行初始化脚本：

```powershell
python -m week10.init_postgresql_schema
```

预期输出类似：

```text
PostgreSQL knowledge schema initialized.
{'vector_extension_ready': True, 'documents_table_ready': True, 'chunks_table_ready': True, 'chunk_embeddings_table_ready': True}
```

然后检查 PostgreSQL 中是否真的创建了表：

```powershell
docker compose exec postgres psql -U agent_user -d agent_db -c "\dt"
```

预期可以看到：

```text
public | chunk_embeddings | table | agent_user
public | chunks           | table | agent_user
public | documents        | table | agent_user
```

验收完成后恢复当前 PowerShell 窗口的环境变量：

```powershell
Remove-Item Env:DATABASE_URL
```

注意：当前后端主业务仍然默认使用 SQLite。PostgreSQL 表结构已经准备好，但文档增删查、Agent 检索、对话记忆等业务链路还没有切换到 PostgreSQL。

## 验证 PostgreSQL/pgvector RAG 存储与检索

当前已经有两个学习 demo 可以验证 PostgreSQL/pgvector 的核心链路。

### 验证 RAG 存储链路

这个 demo 会写入：

- 1 条 document
- 1 条 chunk
- 1 条 1024 维 fake embedding

运行前先确认 PostgreSQL 已经启动，并设置当前 PowerShell 窗口的数据库地址：

```powershell
docker compose up -d postgres
$env:DATABASE_URL="postgresql://agent_user:agent_password@localhost:5432/agent_db"
```

运行：

```powershell
python -m week10.postgresql_rag_storage_demo
```

预期结果中应该看到：

```text
新增文档：
新增片段：
新增 embedding：
embedding_size: 1024
查询到的 embedding 维度： 1024
```

这说明 PostgreSQL 已经可以保存完整的 RAG 数据链路：

```text
document -> chunk -> embedding(vector 1024)
```

### 验证 pgvector 相似度检索

这个 demo 会写入两个测试片段和两个 fake embedding，然后用 query embedding 做向量检索：

```powershell
python -m week10.postgresql_vector_search_demo
```

预期第一条结果是：

```text
员工每天需要完成 8 小时工作。
```

并且第一条结果通常会显示：

```text
距离： 0.0
分数： 1.0
```

这里使用的是 pgvector 的余弦距离运算：

```sql
embedding <=> query_vector
```

距离越小表示越相似。代码里会转换成更直观的分数：

```text
score = 1 - distance
```

### fake embedding 的局限

这些 demo 使用的是 fake embedding，目的是验证 PostgreSQL/pgvector 的存储和检索链路，不代表真实语义效果。

例如，如果 fake embedding 只有第一维不同，两个向量方向可能非常接近，分数也会非常接近 1。真实语义检索需要使用 Ollama 的 `bge-m3` 等 embedding 模型生成 1024 维语义向量。

验收完成后恢复当前 PowerShell 窗口的环境变量：

```powershell
Remove-Item Env:DATABASE_URL
```

注意：当前主业务仍然默认使用 SQLite。PostgreSQL/pgvector 已经完成存储和检索闭环验证，但还没有接入 FastAPI 业务接口和 LangGraph Agent 主链路。

## 验证 PostgreSQL documents 调试接口

当前项目提供了一个 PostgreSQL 调试接口：

```text
GET /api/v1/postgresql/documents
```

这个接口只读取 PostgreSQL `documents` 表，用于确认 FastAPI 可以通过 PostgreSQL repository 读取数据。它不会替代当前 SQLite 主业务接口。

先启动 PostgreSQL：

```powershell
docker compose up -d postgres
```

临时设置当前 PowerShell 窗口的数据库地址：

```powershell
$env:DATABASE_URL="postgresql://agent_user:agent_password@localhost:5432/agent_db"
```

启动后端：

```powershell
python -m uvicorn backend.main:app --reload
```

打开接口文档：

```text
http://127.0.0.1:8000/docs
```

执行：

```text
GET /api/v1/postgresql/documents
```

如果之前运行过 PostgreSQL demo，预期可以看到类似：

```json
[
  {
    "id": 1,
    "title": "PostgreSQL 测试文档",
    "file_type": "md",
    "chunk_count": 0,
    "is_indexed": false
  },
  {
    "id": 2,
    "title": "PostgreSQL RAG 存储测试文档",
    "file_type": "md",
    "chunk_count": 1,
    "is_indexed": true
  }
]
```

验收完成后恢复当前 PowerShell 窗口的环境变量：

```powershell
Remove-Item Env:DATABASE_URL
```

注意：这个接口是 PostgreSQL 调试接口。当前 `/api/v1/db/documents` 仍然是 SQLite 主业务文档接口。

## 验证 PostgreSQL document chunks 调试接口

当前项目也提供了 PostgreSQL chunks 调试接口：

```text
GET /api/v1/postgresql/documents/{document_id}/chunks
```

这个接口只读取 PostgreSQL `chunks` 表，用于确认 FastAPI 可以按文档 id 读取 PostgreSQL 中的文档片段。

确认后端已经用 PostgreSQL `DATABASE_URL` 启动后，在接口文档中执行：

```text
GET /api/v1/postgresql/documents/2/chunks
```

如果之前运行过 PostgreSQL RAG 存储 demo，预期可以看到类似：

```json
[
  {
    "id": 1,
    "document_id": 2,
    "text": "这是一条写入 PostgreSQL pgvector 的测试片段。"
  }
]
```

说明：

- 当前接口返回复用 `Chunk` 模型，所以只显示 `id`、`document_id` 和 `text`。
- PostgreSQL 表里的 `chunk_index` 暂时不会显示在接口返回里。
- 这个接口是 PostgreSQL 调试接口。当前 `/api/v1/db/documents/{document_id}/chunks` 仍然是 SQLite 主业务 chunks 接口。

## 验证 PostgreSQL vector search 调试接口

当前项目提供了 PostgreSQL/pgvector 向量检索调试接口：

```text
POST /api/v1/postgresql/search/vector
```

这个接口接收一个 embedding 数组，然后用 pgvector 从 PostgreSQL 中搜索最相似的 chunks。

注意：PostgreSQL 表中使用的是 `vector(1024)`，所以实际请求必须传入 1024 维 embedding。Swagger 页面不适合手动填写 1024 个数字，推荐使用 demo 脚本验收。

先确认后端已经用 PostgreSQL `DATABASE_URL` 启动：

```powershell
$env:DATABASE_URL="postgresql://agent_user:agent_password@localhost:5432/agent_db"
python -m uvicorn backend.main:app --reload
```

然后另开一个 PowerShell 窗口运行：

```powershell
python -m week10.postgresql_vector_search_api_demo
```

预期输出类似：

```text
状态码： 200
返回结果：
[
  {
    "chunk_id": 2,
    "document_id": 3,
    "document_title": "PostgreSQL 向量检索测试文档",
    "text": "员工每天需要完成 8 小时工作。",
    "distance": 0.0,
    "score": 1.0
  }
]
```

这说明已经打通：

```text
HTTP API -> FastAPI -> PostgreSQL -> pgvector -> 返回检索结果
```

说明：

- 该接口是调试接口，不是最终用户问答接口。
- 它要求调用方直接传入 embedding，不会自动把自然语言问题转换成向量。
- 后续自然语言问答接口会负责调用 embedding 模型，再复用 PostgreSQL/pgvector 检索能力。
- 当前 SQLite/LangGraph 主业务链路仍然没有切换到 PostgreSQL。

## 回填 PostgreSQL chunk embeddings

如果 PostgreSQL 中的 `chunk_embeddings` 是 demo fake embedding，自然语言问题检索结果可能会跑偏。

原因是：

```text
真实问题 embedding -> 匹配 fake chunk embedding -> 语义结果不可靠
```

因此在验证自然语言检索前，需要用 Ollama 的 `bge-m3` 给 PostgreSQL 中已有 chunks 生成真实 embedding。

先确认 PostgreSQL 正在运行：

```powershell
docker compose ps
```

如果 `postgres` 没有运行：

```powershell
docker compose up -d postgres
```

确认本地有 embedding 模型：

```powershell
ollama list
```

应能看到：

```text
bge-m3:latest
```

设置当前 PowerShell 窗口的数据库地址：

```powershell
$env:DATABASE_URL="postgresql://agent_user:agent_password@localhost:5432/agent_db"
```

执行回填：

```powershell
python -m week10.backfill_postgresql_chunk_embeddings
```

一次实际验收输出：

```text
PostgreSQL chunk embedding 回填完成。
总 chunks 数量： 3
更新 embedding 数量： 3
模型： bge-m3:latest
```

说明：

- 该脚本会扫描 PostgreSQL 中所有 chunks。
- 每个 chunk 会调用 Ollama `bge-m3` 生成 1024 维 embedding。
- 写入时使用 upsert：没有 embedding 就新增，已有 embedding 就更新。
- 所以它可以把之前 demo 写入的 fake embedding 覆盖成真实 embedding。

## 验证 PostgreSQL 自然语言检索接口

当前项目提供了自然语言检索调试接口：

```text
POST /api/v1/postgresql/search/question
```

这个接口会完成：

```text
用户问题 -> Ollama bge-m3 生成 embedding -> PostgreSQL pgvector 检索 -> 返回 chunks
```

先用 PostgreSQL `DATABASE_URL` 启动后端：

```powershell
$env:DATABASE_URL="postgresql://agent_user:agent_password@localhost:5432/agent_db"
python -m uvicorn backend.main:app --reload
```

打开接口文档：

```text
http://127.0.0.1:8000/docs
```

执行：

```text
POST /api/v1/postgresql/search/question
```

请求示例：

```json
{
  "question": "员工每天需要工作多久？",
  "top_k": 2
}
```

一次实际验收结果：

```json
{
  "question": "员工每天需要工作多久？",
  "embedding_size": 1024,
  "results": [
    {
      "chunk_id": 2,
      "document_id": 3,
      "document_title": "PostgreSQL 向量检索测试文档",
      "text": "员工每天需要完成 8 小时工作。",
      "distance": 0.1337358951568357,
      "score": 0.8662641048431643
    },
    {
      "chunk_id": 3,
      "document_id": 3,
      "document_title": "PostgreSQL 向量检索测试文档",
      "text": "差旅报销需要在出差结束后 7 天内提交。",
      "distance": 0.5026384153670818,
      "score": 0.49736158463291824
    }
  ]
}
```

验收重点：

- `embedding_size` 应该是 `1024`。
- 第一条结果应该命中相关片段：`员工每天需要完成 8 小时工作。`
- 第一条结果分数明显高于后续不相关片段。

验收结束后恢复当前 PowerShell 窗口的环境变量：

```powershell
Remove-Item Env:DATABASE_URL
```

注意：这个接口已经打通 PostgreSQL 版 RAG 检索链路，但当前 SQLite/LangGraph Agent 主业务链路仍然没有切换到 PostgreSQL。

## 验证 PostgreSQL 文档入库接口

当前项目提供了 PostgreSQL/pgvector 文档入库接口：

```text
POST /api/v1/postgresql/documents/with-content
```

这个接口会完成：

```text
文档正文 -> 切分 chunks -> Ollama bge-m3 生成 embedding -> 写入 PostgreSQL/pgvector
```

先确认 PostgreSQL 已经启动：

```powershell
docker compose up -d postgres
.\scripts\check_postgres.ps1
```

确认 Ollama 已启动，并且本地有 `bge-m3:latest`：

```powershell
ollama list
```

用 PostgreSQL `DATABASE_URL` 启动后端。建议使用项目虚拟环境里的 Python，避免系统 Python 缺少 `uvicorn`：

```powershell
$env:DATABASE_URL="postgresql://agent_user:agent_password@localhost:5432/agent_db"
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8001
```

另开一个 PowerShell 窗口，运行验收脚本：

```powershell
.\.venv\Scripts\python.exe week10\postgresql_document_indexing_api_demo.py
```

预期输出应包含：

```text
创建状态码： 201
检索状态码： 200
```

创建返回中应能看到：

```text
title: PostgreSQL API 入库验收文档
chunk_count: 2
is_indexed: True
```

检索结果 Top 结果应命中新入库文档，例如：

```text
PostgreSQL API 入库验收文档
员工参加外部培训需要提前提交申请。
```

注意：

- 重复运行同一个标题会返回 `409`，这是重复标题保护。
- 如果 Ollama 或 `bge-m3` 不可用，接口会返回 `503`。
- 如果只是临时验收，结束后可以清理当前 PowerShell 窗口的数据库环境变量：

```powershell
Remove-Item Env:DATABASE_URL
```

## 验证 PostgreSQL 检索评测脚本

完成真实 embedding 回填和自然语言检索接口验收后，可以运行 PostgreSQL 检索评测脚本：

```powershell
$env:DATABASE_URL="postgresql://agent_user:agent_password@localhost:5432/agent_db"
python -m week10.evaluate_postgresql_retrieval
```

这个脚本不会调用 LLM 生成回答，只评测检索结果是否命中预期片段。

当前默认评测问题包括：

```text
问题：员工每天需要工作多久？
期望片段：员工每天需要完成 8 小时工作。

问题：差旅报销多久内提交？
期望片段：差旅报销需要在出差结束后 7 天内提交。
```

一次实际验收输出：

```text
PostgreSQL 检索评测完成。
问题数量： 2
通过数量： 2
命中率： 1.0
--------------------------------------------------
问题： 员工每天需要工作多久？
期望片段： 员工每天需要完成 8 小时工作。
Top1 片段： 员工每天需要完成 8 小时工作。
是否通过： True
--------------------------------------------------
问题： 差旅报销多久内提交？
期望片段： 差旅报销需要在出差结束后 7 天内提交。
Top1 片段： 差旅报销需要在出差结束后 7 天内提交。
是否通过： True
```

验收重点：

- `通过数量` 等于问题数量，说明当前样本全部命中。
- `命中率：1.0` 表示当前小评测集检索通过率为 100%。
- `Top1 片段` 命中预期片段，说明正确内容排在第一位。

这一步的价值是把“手动看一次 Swagger 结果”升级为“可以重复运行的检索质量评测”。后续如果修改 chunk 切分、embedding 模型、检索参数或数据库实现，都可以重新运行该脚本检查是否出现退步。

验收结束后恢复当前 PowerShell 窗口的环境变量：

```powershell
Remove-Item Env:DATABASE_URL
```
## 验证 PostgreSQL Retriever 接入 LangGraph Agent

这一步用于验证 PostgreSQL/pgvector 已经接入 LangGraph Agent 的普通问答接口。

完整链路是：

```text
用户问题 -> Ollama bge-m3 embedding -> PostgreSQL pgvector 检索 -> validate_context_node -> answer_node/refuse_node
```

先启动 PostgreSQL：

```powershell
docker compose up -d postgres
.\scripts\check_postgres.ps1
```

确认 PostgreSQL 中已经有真实 chunk embeddings：

```powershell
$env:DATABASE_URL="postgresql://agent_user:agent_password@localhost:5432/agent_db"
python -m week10.evaluate_postgresql_retrieval
```

如果评测没有命中预期片段，先回填 embedding：

```powershell
python -m week10.backfill_postgresql_chunk_embeddings
```

启动后端前，先设置当前 PowerShell 窗口的数据库地址：

```powershell
$env:DATABASE_URL="postgresql://agent_user:agent_password@localhost:5432/agent_db"
```

如果 8000 端口上有旧的 `uvicorn --reload` 进程，接口可能还在跑旧代码。可以临时换到 8001：

```powershell
python -m uvicorn backend.main:app --reload --port 8001
```

打开接口文档：

```text
http://127.0.0.1:8001/docs
```

请求接口：

```text
POST /api/v1/langgraph-agent/chat
```

查询参数：

```text
retriever_backend=postgresql
top_k=2
mode=precomputed_embedding
min_score=0.6
timeout_seconds=30
```

请求体：

```json
{
  "question": "员工每天需要工作多久？"
}
```

验收重点：

```json
{
  "retriever_backend": "postgresql",
  "has_valid_context": true
}
```

引用来源中应出现类似：

```text
postgresql://chunk/2
```

如果返回中 `snippets` 已经命中正确片段，但 `has_valid_context=false`，优先检查后端是否加载了最新代码，必要时换端口重新启动。

如果本次只是临时验收 PostgreSQL，结束后恢复当前 PowerShell 窗口的默认数据库配置：

```powershell
Remove-Item Env:DATABASE_URL
```

## SQLite 到 PostgreSQL 批量迁移流程

这一步用于把当前 SQLite 知识库文档批量迁移到 PostgreSQL/pgvector。迁移脚本默认不会执行写入，必须显式加 `--confirm` 才会真正迁移。

先启动 PostgreSQL 并设置当前 PowerShell 窗口的数据库地址：

```powershell
docker compose up -d postgres
$env:DATABASE_URL="postgresql://agent_user:agent_password@localhost:5432/agent_db"
```

迁移前先预览影响范围：

```powershell
.\.venv\Scripts\python.exe -m week10.preview_sqlite_to_postgresql_migration
```

重点确认：

```text
预计迁移文档数量
预计迁移 chunks 数量
预计生成 embeddings 数量
```

默认运行批量迁移脚本不会写入 PostgreSQL：

```powershell
.\.venv\Scripts\python.exe -m week10.migrate_sqlite_documents_to_postgresql
```

预期输出：

```text
未确认执行批量迁移，已停止。
如需执行，请使用 --confirm
```

确认无误后再执行真实迁移：

```powershell
.\.venv\Scripts\python.exe -m week10.migrate_sqlite_documents_to_postgresql --confirm
```

迁移完成后，必须运行 Agent 验收脚本：

```powershell
.\.venv\Scripts\python.exe -m week10.evaluate_postgresql_migrated_documents_batch
```

理想输出：

```text
问题数量： 5
通过数量： 5
通过率： 1.0
```

最后再跑一次迁移预览，确认没有剩余待迁移文档：

```powershell
.\.venv\Scripts\python.exe -m week10.preview_sqlite_to_postgresql_migration
```

理想输出：

```text
预计迁移文档数量： 0
预计迁移 chunks 数量： 0
预计生成 embeddings 数量： 0
```

注意：

- 不带 `--confirm` 时不会执行迁移。
- 迁移后必须运行 Agent 验收脚本，不能只看写入数量。
- 如果 Agent 验收不是 5/5，先查看失败问题的 TopK 引用来源，再判断是迁移问题还是检索排序问题。
- 迁移写入的文档默认使用 `source=migration`。

## 清理 PostgreSQL evaluation 评测数据

PostgreSQL 文档支持用 `source` 区分数据来源：

```text
production  正式/默认数据
evaluation  评测验收数据
```

评测脚本可能会写入 `source=evaluation` 的文档。清理前建议先预览影响范围。

### 1. 启动 PostgreSQL 并设置数据库地址

```powershell
docker compose up -d postgres
$env:DATABASE_URL="postgresql://agent_user:agent_password@localhost:5432/agent_db"
```

### 2. 先运行清理预览脚本

```powershell
.\.venv\Scripts\python.exe -m week10.preview_postgresql_evaluation_cleanup
```

该脚本只会输出会影响的文档数、chunks 数和 embeddings 数，不会删除数据。

### 3. 也可以通过 API 预览

用 PostgreSQL `DATABASE_URL` 启动后端：

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8001
```

然后访问：

```text
GET /api/v1/postgresql/documents/evaluation/cleanup-preview
```

### 4. 确认后再执行清理

```text
DELETE /api/v1/postgresql/documents/evaluation?confirm=true
```

注意：

- 不带 `confirm=true` 会返回 `400`，不会执行删除。
- 该接口只清理 `source=evaluation` 的文档。
- `source=production` 的正式文档不会被删除。

### 5. 清理后验证

查看 evaluation 文档：

```text
GET /api/v1/postgresql/documents?source=evaluation
```

预期返回空列表：

```json
[]
```

再查看 production 文档：

```text
GET /api/v1/postgresql/documents?source=production
```

如果还能看到正式文档，说明清理没有影响 production 数据。
