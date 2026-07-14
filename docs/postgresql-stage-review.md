# PostgreSQL / pgvector 阶段说明

这份文档记录当前 PostgreSQL 阶段的能力边界。它不是最终项目总结，只用于说明这一阶段已经接通了什么、还保留什么、哪些地方仍然是实验性质。

## 当前已经支持什么

PostgreSQL / pgvector 当前已经接入知识库检索链路：

- 使用 Docker Compose 启动 PostgreSQL + pgvector。
- 初始化 PostgreSQL 知识库表：
  - `documents`
  - `chunks`
  - `chunk_embeddings`
- 将文档内容写入 PostgreSQL，并生成 chunk embeddings。
- 使用 pgvector 做自然语言语义检索。
- LangGraph Agent 可以通过 `retriever_backend=postgresql` 使用 PostgreSQL 检索。
- Streamlit 前端可以切换 PostgreSQL / pgvector 检索后端。
- 带会话保存的 LangGraph Agent 也可以使用 PostgreSQL 检索。

## SQLite 目前还负责什么

PostgreSQL 还没有完全替代 SQLite。

当前 SQLite 仍然负责：

- 默认学习版知识库数据。
- 会话 `conversations`。
- 会话消息 `messages`。
- 会话摘要 `summary`。
- 用户反馈 `feedback`。
- 早期学习阶段的部分 SQLite API。

也就是说，当前项目是混合架构：

```text
知识库语义检索：PostgreSQL / pgvector
会话与反馈状态：SQLite
```

这不是 bug，而是阶段性设计。这样可以先把高价值的向量检索迁到 PostgreSQL，同时保留 SQLite 的轻量状态存储，降低迁移风险。

## 会话保存与 PostgreSQL 检索如何配合

带会话保存的接口：

```text
POST /api/v1/langgraph-agent/conversations/{conversation_id}/chat
```

现在支持：

```text
retriever_backend=postgresql
```

调用时会发生两件事：

1. 知识库检索走 PostgreSQL / pgvector。
2. user/assistant 消息仍保存到 SQLite 的 conversation tables。

因此验收时应该同时看两类结果：

- 引用路径是否类似 `postgresql://chunk/{chunk_id}`。
- 会话消息是否能通过 `GET /api/v1/conversations/{conversation_id}/messages` 查到。

## 当前主要脚本

PostgreSQL Agent 总体验收：

```powershell
.\scripts\check_postgresql_agent.ps1
```

如果不想重复回填 embeddings：

```powershell
.\scripts\check_postgresql_agent.ps1 -SkipEmbeddingBackfill
```

该脚本会检查：

1. PostgreSQL 服务健康状态。
2. PostgreSQL schema 初始化。
3. PostgreSQL chunk embeddings 回填。
4. PostgreSQL 检索评测。
5. PostgreSQL LangGraph Agent 问答评测。
6. PostgreSQL 端到端文档入库 + Agent 问答。
7. PostgreSQL 检索 + SQLite 会话保存链路。

SQLite 到 PostgreSQL 迁移预览：

```powershell
python -m week10.preview_sqlite_to_postgresql_migration
```

SQLite 到 PostgreSQL 批量迁移：

```powershell
python -m week10.migrate_sqlite_documents_to_postgresql --confirm
```

PostgreSQL evaluation 数据清理预览：

```powershell
python -m week10.preview_postgresql_evaluation_cleanup
```

## 当前还不是生产级的地方

这一阶段仍然是工程学习版，不是完整企业生产落地版。

主要缺口包括：

- 还没有把所有业务状态统一迁移到 PostgreSQL。
- 会话保存仍然是 SQLite，没有使用 PostgreSQL 管理全部业务数据。
- pgvector 检索参数还主要靠手动评测调试。
- 没有权限系统、租户隔离、审计日志和企业级数据治理。
- 没有完整的后台任务队列来处理大批量文档入库和 embedding 回填。
- 没有真正的生产级监控、告警和灰度发布流程。

## 当前阶段结论

当前项目已经完成了 PostgreSQL / pgvector 从“数据库准备”到“可用于 Agent 检索”的阶段跃迁。

但它还不是“全量 PostgreSQL 生产架构”。更准确的说法是：

```text
PostgreSQL / pgvector 已经成为可选知识库检索后端；
SQLite 仍然承担默认学习数据、会话和反馈等轻量状态。
```

后续如果继续推进，可以逐步考虑：

- 将 conversations / messages / feedback 迁移到 PostgreSQL。
- 抽象统一 repository 层。
- 增加更系统的检索评测集。
- 增加权限、审计、任务队列和运维监控。
