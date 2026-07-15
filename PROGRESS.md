# 学习进度

最后更新：2026-07-15

## 当前阶段

当前已经进入：

```text
阶段 6：Agent 工程化与交付前收口
```

项目已经完成企业知识库 Agent 的主要工程闭环：

- FastAPI 后端
- Streamlit 前端
- SQLite 默认知识库与会话状态
- PostgreSQL / pgvector 可选检索后端
- RAG 引用问答
- LangGraph Agent
- 会话上下文增强
- 文档入库与 embedding 回填
- 统一评测脚本
- 后台任务中心
- Docker build
- GitHub Actions
- README / runbook / API 文档

## 当前稳定状态

最近一次本地交付前验收：

```text
check_project.ps1 通过
check_rag_evaluation_ci.ps1 通过
check_docker_build.ps1 通过
GitHub Actions 绿色
```

## 已掌握能力

- 能读懂并维护 FastAPI 项目结构。
- 能把业务逻辑拆到 service / repository / router。
- 能用 pytest 为功能建立回归保护。
- 能设计 RAG 检索、引用和拒答逻辑。
- 能使用 LangGraph 表达 Agent 工作流。
- 能通过 steps 观察 Agent 执行过程。
- 能区分检索失败、上下文无效、生成失败和超时兜底。
- 能使用 SQLite 保存轻量状态。
- 能使用 PostgreSQL / pgvector 做语义检索。
- 能设计文档入库、chunk、embedding、回填、迁移和清理流程。
- 能用脚本做本地验收。
- 能用 GitHub Actions 做持续集成。
- 能用 Docker Compose 做构建和服务验证。
- 能区分学习版 Demo、工程化项目和生产级系统之间的差距。

## 当前仍未生产化的能力

- 权限系统
- 租户隔离
- 审计日志
- 生产级任务队列
- 统一 PostgreSQL 业务状态存储
- 大规模文档解析和性能压测
- 生产级监控和告警
- 完整长期记忆系统

## 下一阶段建议

下一阶段建议主题：

```text
从本地工程学习项目，走向生产化 Agent 后端雏形。
```

优先推进方向：

1. 任务记录持久化到 PostgreSQL。
2. 文档入库和 embedding 回填任务 worker 化。
3. 扩展 RAG evaluation cases。
4. 引入权限、审计和多用户边界。
5. 明确 SQLite 与 PostgreSQL 的最终职责划分。

更多阶段总结见：

- [项目阶段总结](docs/project-stage-summary.md)
- [运行手册](docs/runbook.md)
- [PostgreSQL 阶段说明](docs/postgresql-stage-review.md)
