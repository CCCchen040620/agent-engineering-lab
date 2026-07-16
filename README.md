# Enterprise Knowledge Agent Engineering Lab

这是一个从零开始演进出来的企业知识库 Agent 学习项目。项目目标不是做一个玩具问答 Demo，而是把企业知识问答常见的工程问题逐步拆开：文档入库、chunk 切分、关键词检索、向量检索、RAG 引用回答、Agent 工作流、会话上下文、PostgreSQL/pgvector、评测脚本、后台任务和交付验收。

当前项目已经进入“交付前收口阶段”：核心链路可以跑通，本地测试和 CI 都已经建立，剩下的重点是文档、验收体验和生产化边界说明。

## 当前能力

项目当前支持：

- FastAPI 后端接口
- Streamlit 用户页面
- SQLite 默认知识库和会话状态存储
- PostgreSQL / pgvector 作为可选知识库检索后端
- Markdown / TXT 文档入库、chunk 切分和 embedding 生成
- Ollama 本地模型调用
  - 默认 LLM：`qwen3.6:latest`
  - 默认 embedding 模型：`bge-m3:latest`
- 普通 RAG 问答
- Simple Agent 问答
- LangGraph Agent 问答
- LangGraph 会话保存问答
- PostgreSQL 文档入库、检索、迁移和清理能力
- RAG / Agent 评测脚本
- 任务中心：支持 PostgreSQL 文档入库任务、embedding 回填任务、失败诊断、事件时间线和失败任务重试
- Docker Compose 构建和 PostgreSQL 服务
- GitHub Actions：pytest、轻量 RAG evaluation、Docker build

## 架构概览

默认模式下，项目使用 SQLite 作为轻量本地数据存储：

```text
用户问题
  -> Streamlit / FastAPI
  -> LangGraph Agent
  -> SQLite 文档 chunks / 预计算 embeddings
  -> Ollama 生成回答
  -> 返回 answer + citations + steps
```

PostgreSQL 模式下，知识库语义检索可以切换到 pgvector：

```text
用户问题
  -> Ollama bge-m3 生成 query embedding
  -> PostgreSQL / pgvector 检索 chunks
  -> LangGraph Agent 校验上下文
  -> Ollama 生成回答
  -> 返回 postgresql://chunk/{id} 引用来源
```

当前是混合架构：

- 知识库检索：SQLite 或 PostgreSQL / pgvector
- 会话、消息、反馈等轻量状态：仍主要使用 SQLite
- PostgreSQL 已经可用于 RAG 检索和文档入库，但还不是全量生产数据库替代方案

## 快速开始

### 1. 准备环境

项目使用 Python 3.13：

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

如果你只是第一次检查本机环境，可以运行：

```powershell
.\scripts\check_environment.ps1
```

如果不知道该跑哪个验收命令，先看命令菜单：

```powershell
.\scripts\list_project_checks.ps1
```

### 2. 准备 Ollama 模型

本地需要启动 Ollama，并准备模型：

```powershell
ollama list
```

默认配置使用：

```text
qwen3.6:latest
bge-m3:latest
```

配置项见 [.env.example](.env.example) 和 [docs/configuration.md](docs/configuration.md)。

### 3. 运行基础检查

日常本地回归：

```powershell
.\scripts\check_project.ps1
```

该脚本会运行 SQLite schema 迁移和完整测试。

也可以直接运行：

```powershell
pytest
```

### 4. 启动本地应用

启动 FastAPI 后端：

```powershell
.\scripts\start_backend.ps1
```

接口文档：

```text
http://127.0.0.1:8000/docs
```

另开一个 PowerShell 窗口启动 Streamlit：

```powershell
.\scripts\start_frontend.ps1
```

用户页面：

```text
http://127.0.0.1:8501
```

常用管理页：

```powershell
python -m streamlit run frontend/admin_documents.py
python -m streamlit run frontend/admin_tasks.py
```

## PostgreSQL / pgvector 模式

启动 PostgreSQL：

```powershell
docker compose up -d postgres
.\scripts\check_postgres.ps1
```

设置当前窗口的数据库地址：

```powershell
$env:DATABASE_URL="postgresql://agent_user:agent_password@localhost:5432/agent_db"
```

初始化 PostgreSQL 知识库 schema：

```powershell
.\.venv\Scripts\python.exe -m week10.init_postgresql_schema
```

运行 PostgreSQL Agent 验收：

```powershell
.\scripts\check_postgresql_agent.ps1 -SkipConversationChat -SkipIngestedDocumentCheck
```

如果要跑批量文档入库 Agent 验收：

```powershell
.\scripts\check_postgresql_agent.ps1 -RunBatchDocumentIngestionCheck
```

运行任务中心专项验收：

```powershell
.\scripts\check_task_center.ps1
```

该脚本会验证 PostgreSQL 文档异步入库、任务结果详情、失败诊断、`task_failed` 事件中的 `metadata.error`，以及失败任务重试链路。

说明：PostgreSQL 模式依赖 Docker PostgreSQL、pgvector、Ollama 和 embedding 模型。它适合做企业级检索后端实验，但当前项目仍保留 SQLite 负责部分轻量状态。

## 评测与报告

轻量 RAG 评测：

```powershell
.\scripts\check_rag_evaluation_ci.ps1
```

完整 RAG 评测：

```powershell
.\scripts\check_rag_evaluation.ps1
```

默认运行生成的本地报告会写入：

```text
.local/evaluations/
```

该目录已被 `.gitignore` 忽略，避免评测报告污染工作区。如果要把某次报告作为正式记录，可以显式传入 `--report-path docs/evaluations/xxx.md`。

## Docker

构建镜像：

```powershell
.\scripts\check_docker_build.ps1
```

启动完整 Compose 服务：

```powershell
docker compose up --build
```

验收 Compose 服务：

```powershell
.\scripts\check_docker_compose.ps1
```

注意：当前 Docker Compose 默认不会把 Ollama 放入容器，而是访问宿主机 Ollama。

## 主要目录

```text
backend/        FastAPI routers、服务层、数据库访问、Agent 工具
frontend/       Streamlit 用户页面和管理页面
week08-11/      学习阶段脚本、迁移脚本、评测脚本
docs/           API、配置、运行手册、阶段复盘和评测用例
scripts/        本地启动、检查、迁移和验收脚本
tests/          自动化测试
```

## 项目文档

- [运行手册](docs/runbook.md)
- [API 文档](docs/api.md)
- [配置说明](docs/configuration.md)
- [最终交付状态盘点](docs/final-delivery-review.md)
- [项目阶段总结](docs/project-stage-summary.md)
- [前端说明](docs/frontend.md)
- [PostgreSQL 阶段说明](docs/postgresql-stage-review.md)
- [LangGraph Agent 阶段复盘](docs/langgraph-agent-stage-review.md)
- [Agent 阶段 checklist](docs/agent-stage-checklist.md)
- [学习路线](LEARNING_PLAN.md)
- [学习进度](PROGRESS.md)

## 当前边界

这是一个工程学习项目，不是生产可直接上线版本。当前主要边界包括：

- 没有完整权限系统、租户隔离和企业级审计
- 没有生产级任务队列；任务中心仍是轻量学习版
- PostgreSQL 已接入知识库检索和入库，但会话、反馈等状态仍主要在 SQLite
- 长期记忆仍是有限上下文增强，不是完整用户画像或跨会话记忆系统
- LLM 生成质量受本地 Ollama 模型状态影响，评测中会区分检索层和生成层结果
- 部分管理页面用于本地验收，不代表最终产品 UI

## 推荐工作流

日常开发：

```powershell
.\scripts\list_project_checks.ps1
.\scripts\check_project.ps1
```

涉及 PostgreSQL / pgvector：

```powershell
docker compose up -d postgres
.\scripts\check_postgres.ps1
.\scripts\check_postgresql_agent.ps1 -SkipConversationChat -SkipIngestedDocumentCheck
```

交付前：

```powershell
.\scripts\check_project.ps1
.\scripts\check_rag_evaluation_ci.ps1
.\scripts\check_docker_build.ps1
```

如果需要完整本地业务验收，再运行任务中心专项验收、PostgreSQL Agent 检查和完整 RAG evaluation。
