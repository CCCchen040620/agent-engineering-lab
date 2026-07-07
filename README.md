# 企业知识库 Agent：从零开始的学习项目

这里不是一个需要你直接复制的成品，而是一套会和你一起成长的代码。

我们将用约 20 周，从第一个 Python 程序出发，逐步完成一个能上传文档、检索知识、调用工具、给出引用并在线演示的企业知识库 Agent。

## 现在只做这一件事

完成第 1 周的第 1 课：

1. 打开 Windows 终端。
2. 输入 `python --version`，确认能看到 `Python 3.13.x`。
3. 在当前目录输入：

   ```powershell
   python week01/hello_agent.py
   ```

4. 按提示输入你的名字和学习目标。
5. 如果环境检查未完成，先打开 [环境检查单](week01/environment-checklist.md)。
6. 打开 [第 1 周课程](week01/README.md)，完成今天的练习。

如果 `python` 命令不可用，可以尝试：

```powershell
py -3.13 week01/hello_agent.py
```

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

当前状态：**已完成 FastAPI、SQLite、RAG、Ollama、Streamlit 的基础闭环，正在进行工程化整理**

## 当前项目快速运行

现在项目已经具备 FastAPI 后端、Streamlit 前端、SQLite 知识库、本地 Ollama 大模型和 embedding 检索能力。

推荐启动顺序：

1. 确认 Ollama 已启动，并且本地模型可用。

   ```powershell
   ollama list
   ```

   当前项目默认使用：

   - `qwen3.6:latest`：用于生成回答
   - `bge-m3:latest`：用于生成 embeddings

2. 启动 FastAPI 后端。

   ```powershell
   .\scripts\start_backend.ps1
   ```

   接口文档地址：

   ```text
   http://127.0.0.1:8000/docs
   ```

3. 另开一个 PowerShell 窗口，启动 Streamlit 用户页面。

   ```powershell
   .\scripts\start_frontend.ps1
   ```

4. 如需查看管理页面，可以再启动：

   ```powershell
   .\scripts\start_admin_documents.ps1
   .\scripts\start_admin_feedback.ps1
   ```

5. 运行测试：

   ```powershell
   pytest
   ```

更多运行和排错说明见 [项目运行手册](docs/runbook.md)。
