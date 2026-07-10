# 企业知识库 Agent：从零开始的学习项目

这里不是一个需要你直接复制的成品，而是一套会和你一起成长的代码。

我们将用约 20 周，从第一个 Python 程序出发，逐步完成一个能上传文档、检索知识、调用工具、给出引用并在线演示的企业知识库 Agent。

## 当前学习阶段

本仓库最初从第 1 周的 Python 入门练习开始，目前已经推进到企业知识库 Agent 的核心工程化阶段。

当前稳定状态：

```text
337 passed, 1 warning
```

当前已经具备：

- FastAPI 后端接口
- SQLite 文档、chunks、feedback、conversation 存储
- RAG 检索与引用回答
- Ollama 本地大模型回答
- `bge-m3` embedding 检索
- Streamlit 用户页面和管理页面
- LangGraph Agent 流程编排
- 基于 conversation messages 的有限上下文检索增强
- SQLite schema 迁移脚本
- pytest 自动化测试

## 学习原则

- 每次只学习解决当前问题所需的知识。
- 先自己尝试，再看提示，最后才看完整答案。
- 报错不是失败，而是开发环境在给我们线索。
- 每周必须留下代码、测试、学习记录和一次 Git 提交。
- 没通过阶段验收，不急着追赶日期。

## 项目地图

- [20 周路线图](LEARNING_PLAN.md)
- [学习进度](PROGRESS.md)
- [学习日志](docs/learning-log.md)
- [错误档案](docs/error-log.md)
- [英文术语卡](docs/glossary.md)
- [师生协作方式](MENTORING.md)
- [当前 API 文档](docs/api.md)
- [项目运行手册](docs/runbook.md)
- [前端说明](docs/frontend.md)
- [配置说明](docs/configuration.md)

当前状态：**已完成 FastAPI、SQLite、RAG、Ollama、Streamlit、LangGraph Agent 的基础闭环，正在继续完善工程化与长期记忆能力。**

## 当前项目快速运行

现在项目已经具备 FastAPI 后端、Streamlit 前端、SQLite 知识库、本地 Ollama 大模型和 embedding 检索能力。

### 1. 本地健康检查

每次开始开发或收工前，建议运行：

```powershell
.\scripts\check_project.ps1
```

该脚本会依次执行：

1. SQLite schema 迁移
2. pytest 全量测试

如果 PowerShell 不允许运行脚本，可以使用：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check_project.ps1
```

### 2. 启动项目

推荐启动顺序：

1. 确认 Ollama 已启动，并且本地模型可用。

   ```powershell
   ollama list
   ```

   当前项目默认使用：

   - `qwen3.6:latest`：用于生成回答
   - `bge-m3:latest`：用于生成 embeddings

2. 迁移 SQLite schema。

   ```powershell
   .\scripts\migrate_sqlite.ps1
   ```

3. 启动 FastAPI 后端。

   ```powershell
   .\scripts\start_backend.ps1
   ```

   接口文档地址：

   ```text
   http://127.0.0.1:8000/docs
   ```

4. 另开一个 PowerShell 窗口，启动 Streamlit 用户页面。

   ```powershell
   .\scripts\start_frontend.ps1
   ```

5. 如需查看管理页面，可以再启动：

   ```powershell
   .\scripts\start_admin_documents.ps1
   .\scripts\start_admin_feedback.ps1
   ```

6. 也可以单独运行测试：

   ```powershell
   pytest
   ```

### 3. 当前能力边界

当前 LangGraph Agent 已经支持基于同一 `conversation_id` 的有限上下文增强：

- assistant 消息会保存 `citations`、`steps`、`intent`、`keyword` 等 metadata。
- 后续问题可以基于最近引用文档构造 `contextual_question`。
- 检索结果会按最近引用文档过滤，减少无关引用混入。
- 如果当前问题和历史上下文不相关，Agent 会拒答，避免上下文污染。

但它还不是完整长期记忆系统：

- 还没有长期摘要记忆
- 还没有用户画像或偏好记忆
- 还没有跨会话记忆
- 还没有把全部历史消息交给模型做复杂多轮推理

更多运行和排错说明见 [项目运行手册](docs/runbook.md)。
