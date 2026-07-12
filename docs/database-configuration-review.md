# 数据库路径配置化阶段小结

这份文档记录本轮数据库路径配置化的工程化收口。

它不是最终项目总结，也不是简历包装文档，只是给当前学习阶段留一份可回看的复盘。

## 为什么要做这一步

项目早期很多后端代码直接依赖旧配置：

```text
SQLITE_DATABASE_PATH
```

这种写法在学习早期很直观，但项目变大之后会带来几个问题：

- 数据库路径分散在旧配置里，维护成本变高。
- 测试环境、Docker 环境、本地环境容易读到不同数据库。
- 后续迁移 PostgreSQL / pgvector 时，不方便统一切换。
- 新代码可能继续复制旧写法，导致配置越来越乱。

所以这一轮的目标不是立刻把 SQLite 换成 PostgreSQL，而是先把数据库地址集中管理起来。

## 现在的做法

当前数据库配置入口是：

```text
DATABASE_URL
```

默认值是：

```text
sqlite:///data/app.db
```

代码内部会从 `DATABASE_URL` 推导出：

```text
DATABASE_PATH=data/app.db
```

也就是说：

- `DATABASE_URL` 是对外配置入口。
- `DATABASE_PATH` 是当前 SQLite 阶段使用的内部路径。
- 后续如果切换 PostgreSQL，可以继续沿用 `DATABASE_URL` 这个统一入口。

## 已迁移范围

本轮已经把后端主数据库链路逐步迁移到 `DATABASE_PATH`：

- 系统状态检查
- SQLite schema 迁移脚本
- DB Documents API 的公共数据库路径依赖
- Feedback API
- Agent Tools
- Simple Agent
- LangGraph Agent
- SQLite 基础 QA 服务
- SQLite LLM RAG QA 服务

迁移方式是小步推进：

1. 先迁移一个文件或一层能力。
2. 增加对应测试。
3. 跑局部测试。
4. 跑全量测试。
5. 再提交。

这种做法虽然慢一点，但风险更低，也更适合你现在边学边做。

## 防回退测试

本轮新增了防回退测试：

```text
tests/test_backend_configuration_guards.py
```

它会检查 `backend/` 目录中是否重新出现：

```text
SQLITE_DATABASE_PATH
```

如果以后后端主流程不小心又引入旧路径写法，测试会失败。

这类测试不是为了验证某个接口返回什么，而是为了守住项目结构规则。

## 当前没有做什么

这一轮还没有做这些事情：

- 没有把 SQLite 替换成 PostgreSQL。
- 没有接入 pgvector。
- 没有改造全部 repository 抽象。
- 没有删除早期学习阶段的 `week04.settings`。
- 没有迁移早期 JSON 文档接口里的 `DOCUMENTS_JSON_PATH`。

其中 `backend/routers/documents.py` 仍然引用 `DOCUMENTS_JSON_PATH`，这是早期 JSON 文档接口的文件路径，不属于本轮数据库路径迁移范围。

## 学到的工程化思想

这一步对应几个真实项目里很常见的工程化思想：

- 配置不要散落在业务代码里。
- 环境差异应该通过配置解决，而不是到处改代码。
- 迁移不要一次性大改，应该小步、有测试地推进。
- 除了功能测试，也要有结构性防回退测试。
- 先把 SQLite 路径统一起来，是后续 PostgreSQL / pgvector 迁移的前置准备。

这一轮完成后，项目离“可配置、可部署、可迁移”的方向更近了一步。
