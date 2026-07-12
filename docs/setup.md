# 项目安装说明

本文档用于第一次在本地准备企业知识库 Agent 项目环境。

日常启动、验收和排错请查看 [项目运行手册](runbook.md)。

## 1. 环境要求

- Windows 电脑
- Python 3.13
- Git
- Ollama
- 建议至少 16GB 内存

当前项目的目标 Python 版本是 3.13。项目配置、Docker 镜像和 GitHub Actions 都按 Python 3.13 对齐。

在 Windows 上可以先检查默认 Python：

```powershell
python --version
```

如果这里显示的不是 Python 3.13，再检查 Python Launcher 是否能找到 3.13：

```powershell
py -3.13 --version
```

如果 `py -3.13` 可以正常显示版本，后面创建虚拟环境时优先使用 `py -3.13`，不要直接使用默认 `python`。

如果提示找不到 `py` 或找不到 Python 3.13，说明本机还没有正确安装或配置 Python 3.13。后续最终交付前建议重新安装 Python 3.13，并在安装时勾选 “Add python.exe to PATH”。

当前项目使用的本地模型：

```text
qwen3.6:latest  用于生成回答
bge-m3:latest   用于生成 embeddings
```

可以用下面命令检查 Ollama 模型：

```powershell
ollama list
```

## 2. 创建虚拟环境

在项目根目录运行：

```powershell
py -3.13 -m venv .venv
```

如果你的默认 `python` 已经是 3.13，也可以使用：

```powershell
python -m venv .venv
```

激活虚拟环境：

```powershell
.\.venv\Scripts\Activate.ps1
```

如果 PowerShell 不允许运行脚本，可以临时放开当前窗口的执行策略：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

然后重新激活虚拟环境。

## 3. 安装依赖

安装项目运行依赖和开发测试依赖：

```powershell
python -m pip install -e ".[dev]"
```

项目核心依赖在 [pyproject.toml](../pyproject.toml) 中维护，包括：

- FastAPI
- Uvicorn
- Pydantic
- Streamlit
- LangGraph
- jieba
- requests
- python-multipart

## 4. 迁移 SQLite schema

如果需要查看可配置项，可以先复制配置模板：

```powershell
Copy-Item .env.example .env
```

当前项目启动时会自动读取 `.env` 文件。实际运行时如需覆盖配置，可以修改 `.env`，也可以参考 [配置说明](configuration.md) 在 PowerShell 中临时设置环境变量。

首次运行，或更新代码后涉及数据库字段变化时，运行：

```powershell
.\scripts\migrate_sqlite.ps1
```

如果 PowerShell 不允许运行脚本，可以使用：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\migrate_sqlite.ps1
```

该脚本会创建或补齐 conversation/message 相关表结构。

## 5. 运行健康检查

第一次准备环境时，建议先运行：

```powershell
.\scripts\check_environment.ps1
```

它会检查本机命令、关键项目文件，并提示当前 Python 是否与项目目标版本 3.13 对齐。

推荐运行：

```powershell
.\scripts\check_project.ps1
```

该脚本会先迁移 SQLite schema，再运行 pytest。

当前稳定测试状态：

```text
449 passed, 1 warning
```

## 6. 启动项目

启动后端：

```powershell
.\scripts\start_backend.ps1
```

接口文档：

```text
http://127.0.0.1:8000/docs
```

启动 Streamlit 用户页面：

```powershell
.\scripts\start_frontend.ps1
```

可选启动管理页面：

```powershell
.\scripts\start_admin_documents.ps1
.\scripts\start_admin_feedback.ps1
```

## 7. 常见说明

- `data/app.db` 是本地运行时 SQLite 数据库，不提交到 Git。
- 如果接口返回数据库字段相关错误，先运行 `.\scripts\migrate_sqlite.ps1`。
- 如果 Windows 上 `uvicorn --reload` 返回旧逻辑，可以参考 [项目运行手册](runbook.md) 中的后端旧进程排查。
- 当前 conversation 能力属于有限上下文增强，还不是完整长期记忆系统。
