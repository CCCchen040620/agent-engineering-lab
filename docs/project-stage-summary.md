# 项目阶段总结：企业知识库 Agent 工程化收口

## 任务中心当前边界

当前任务中心已经完成了基础工程闭环：

- PostgreSQL 可保存任务记录。
- 支持 PostgreSQL embedding 回填任务。
- 支持 PostgreSQL 文档异步入库任务。
- 任务列表默认最新任务优先。
- 失败任务具备结构化错误原因和处理建议。
- 任务具备轻量进度字段：`progress_percent` 和 `progress_message`。
- 失败任务可以异步重试，并通过 `retry_of_task_id` 保留来源链路。
- 任务可以记录 `run_count` 和 `retry_count`，用于观察运行和重试统计。
- 任务详情可以查看事件时间线，用于回溯创建、开始、成功、失败、取消和重试派生。
- 事件时间线可以展示失败诊断摘要，并通过 `retry_task_id` 追踪派生重试任务。
- `pending` 任务可以取消，`running` 任务暂不强行中断。
- 已提供 `.\scripts\check_task_center.ps1` 作为任务中心专项验收脚本。

但它仍然不是生产级任务队列系统。当前异步执行仍依赖 FastAPI 进程内轻量线程，还没有独立 worker、自动重试策略、运行中任务取消、并发控制和分布式队列。后续如果继续生产化，任务中心可以作为过渡层，最终再接入 Redis / Celery / RQ / Dramatiq 等真实队列方案。

任务中心专项验收已经通过。推荐验收命令是：

```powershell
.\scripts\check_task_center.ps1
```

该验收覆盖了当前阶段最关键的后台任务链路：PostgreSQL 文档异步入库、任务结果详情、失败诊断、`task_failed` 事件中的 `metadata.error`、失败任务异步重试，以及 `retry_task_id` 追踪。也就是说，任务中心当前已经达到“本地交付前可验收”的学习项目状态。

下一阶段如果继续往生产化推进，不建议直接在当前 FastAPI 进程内线程上无限加功能，而应该把重点转向独立 worker、真实队列、自动重试策略、并发控制、运行中任务取消和更完整的审计记录。

截至当前阶段，这个项目已经从“学习型 Demo”推进到了“可验收的工程学习项目”。

它还不是生产级企业 Agent，但已经具备一套完整的本地工程闭环：文档入库、检索、RAG 引用回答、Agent 编排、会话上下文、PostgreSQL/pgvector 检索、评测脚本、后台任务、Docker 构建、CI 和运行手册。

## 1. 当前学习阶段判断

你现在已经不在 Python 入门、普通后端接口或单点 RAG Demo 阶段。

更准确地说，当前处于：

```text
阶段 6：Agent 工程化与交付前收口
```

这个阶段的核心能力不是“会不会调用大模型”，而是：

- 能不能把一个 Agent 项目拆成清晰模块
- 能不能让检索、生成、存储、前端、评测和部署脚本协同工作
- 能不能通过测试和脚本反复验收同一条业务链路
- 能不能区分 Demo 能力、工程能力和生产化缺口

这也是从“会写功能”进入“能维护一个项目”的关键分水岭。

## 2. 当前已经完成的工程能力

### 后端与前端

- FastAPI 后端接口已经成型。
- Streamlit 用户页面可以进行 RAG / Agent 问答。
- 文档管理、任务中心等管理页面已经具备本地验收价值。
- 系统状态、检索后端、Agent steps、引用来源等关键调试信息可以在页面中观察。

### RAG 与 Agent

- 支持关键词检索、向量检索、embedding 检索、预计算 embedding 检索。
- 支持普通 RAG 问答。
- 支持 Simple Agent 问答。
- 支持 LangGraph Agent 问答。
- LangGraph Agent 已经具备：
  - intent routing
  - 文档列表 / 文档读取 / 知识库问答分流
  - context validation
  - refusal fallback
  - timeout fallback
  - generation fallback
  - steps 可观测性
  - 会话上下文补全
  - PostgreSQL retriever 切换

### 数据与检索后端

- SQLite 负责默认学习版数据、会话、消息、反馈等轻量状态。
- PostgreSQL / pgvector 已经接入知识库检索链路。
- PostgreSQL 支持：
  - documents / chunks / chunk_embeddings schema
  - 文档入库
  - chunk embedding 回填
  - pgvector 语义检索
  - source 区分 production / evaluation / migration
  - evaluation 数据清理
  - SQLite 到 PostgreSQL 批量迁移

### 评测与验收

- 本地全量测试已稳定通过。
- GitHub Actions 已绿色通过。
- CI 覆盖：
  - pytest
  - 轻量 RAG evaluation
  - Docker build
- 本地脚本已经分层：
  - 本地快速检查
  - PostgreSQL 检查
  - 交付前完整检查
- RAG evaluation 已经区分：
  - 业务通过率
  - 检索通过率
  - 生成通过率
  - 端到端通过率
- 评测报告默认输出到 `.local/evaluations/`，不会污染 Git 工作区。

## 3. 这个项目已经不再只是 Demo 的原因

它仍然是学习项目，但已经不是“只跑一个问答效果”的简单 Demo。

原因是项目已经具备以下工程特征：

- 有明确的模块边界：router、service、repository、frontend、scripts、tests。
- 有可重复运行的测试体系。
- 有 Docker 构建验证。
- 有 CI。
- 有数据迁移脚本。
- 有评测脚本。
- 有 runbook。
- 有本地脚本入口。
- 有对失败状态的处理：拒答、超时、生成失败、检索无结果。
- 有对上下文污染、无答案问题、prompt injection 类问题的基础评测意识。

这说明你已经开始学习真实工程项目中最重要的一部分：让功能可以被反复验证，而不是只在某次手动操作中偶然成功。

## 4. 当前还不是生产级的地方

当前项目还没有达到真实企业生产级 Agent 的要求。主要缺口包括：

- 没有权限系统。
- 没有租户隔离。
- 没有完整审计日志。
- 没有用户身份体系。
- 没有生产级任务队列和 worker。
- 没有统一把所有业务状态迁移到 PostgreSQL。
- 没有完整的后台管理系统。
- 没有生产级监控、告警、Tracing。
- 没有灰度发布、回滚和多环境部署流程。
- 没有大规模文档集下的性能压测。
- 没有对真实企业文档格式的完整解析能力。
- 长期记忆仍是有限上下文增强，不是完整用户画像或跨会话长期记忆系统。

这些不是失败，而是下一阶段方向。

## 5. 下一阶段最值得做什么

如果继续往企业级 Agent 推进，建议不要继续盲目加功能，而是按优先级推进。

### 优先级 1：生产化数据边界

目标：让数据模型更接近真实系统。

可以继续做：

- 将任务记录从内存迁移到 PostgreSQL。
- 明确 conversation / message / feedback 是否继续留在 SQLite，还是逐步迁移到 PostgreSQL。
- 给 PostgreSQL 增加更完整的 migration 管理。
- 给 documents / chunks / embeddings 增加更清晰的数据生命周期。

### 优先级 2：任务队列与异步处理

目标：让文档入库和 embedding 回填更像真实后台任务。

可以继续做：

- PostgreSQL 保存 task 状态。
- 后台 worker 执行任务。
- 支持任务进度。
- 支持失败重试。
- 支持取消任务。
- 后续再考虑 Redis / Celery / RQ / Dramatiq 这类真正队列。

### 优先级 3：评测体系升级

目标：从“样例评测”升级为“持续质量门禁”。

可以继续做：

- 扩展 RAG cases。
- 增加多行业通用 case schema。
- 增加 expected citation、expected refusal、expected no-retrieval 等更明确字段。
- 将生成质量和检索质量分开打分。
- 为 CI 保留轻量评测，为本地保留完整评测。

### 优先级 4：安全与权限

目标：让系统开始具备企业级边界意识。

可以继续做：

- 用户身份。
- 文档权限。
- 会话权限。
- 管理员和普通用户区分。
- 操作审计。
- 防 prompt injection 的策略评测。

## 6. 当前阶段结论

这一阶段最大的成果不是某一个功能，而是你已经完成了一次完整的工程闭环：

```text
需求理解
-> 功能拆分
-> 测试驱动
-> 本地实现
-> 前端接入
-> 文档同步
-> 脚本验收
-> CI 验证
-> 阶段收口
```

这条链路比单纯“会写 RAG”重要得多。

你现在已经具备继续学习企业级 Agent 工程的基础：能看懂项目结构，能理解检索与生成的边界，能通过测试定位问题，也能把功能逐步收口成可验收状态。

下一阶段如果继续推进，建议主题定为：

```text
从本地工程学习项目，走向生产化 Agent 后端雏形。
```
