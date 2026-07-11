# Streamlit 网页界面说明

本项目提供了一个基于 Streamlit 的网页界面，用于演示企业知识库 Agent 的 RAG 问答能力。

## 启动前准备

请先确认：

- SQLite 数据库 `data/app.db` 已存在
- Ollama 已启动
- 本地模型 `qwen3.6:latest` 可用

可以使用下面命令查看本地模型：

```powershell
ollama list
```

## 页面功能

当前页面支持：

- 在侧边栏展示系统状态诊断，包括 API、SQLite、Ollama、LLM 模型和 Embedding 模型状态。
- 输入企业知识库问题
- 提问时会调用 FastAPI 后端接口 `POST /api/v1/db/chat/llm`，由后端完成检索、组装提示词和调用本地大模型。
- 可切换问答引擎：
  - `普通 RAG 问答`：调用 `POST /api/v1/db/chat/llm`
  - `Simple Agent 问答`：调用 `POST /api/v1/agent/chat`
  - `LangGraph Agent 问答`：默认调用 `POST /api/v1/langgraph-agent/chat`
- Simple Agent 会先判断用户意图，再选择工具：
  - 文档列表类问题会调用 `list_documents_tool`
  - 读取文档类问题会调用 `find_document_by_title_tool` 和 `read_document_chunks_tool`
  - 如果读取文档类问题缺少文档标题，会调用 `ask_clarification_tool` 进行澄清
  - 普通业务问题会调用 `search_knowledge_base_tool`，再回答或拒答
- Simple Agent 模式会展示 `steps`，用于观察 Agent 的意图判断、工具选择、搜索、回答或拒答过程。
  - `tool`：本步骤调用的工具
  - `input`：工具输入
  - `observation`：工具执行后的观察结果
    - 读取文档时，`observation.match_type` 会显示标题匹配方式，例如 `exact` 或 `contains`
  - `next_action`：Agent 决定的下一步动作
- 可以在 Simple Agent 模式下尝试提问：“知识库里有哪些文档？”
- 也可以尝试：“查看员工手册的片段” 或 “查看这份文档的片段”
- LangGraph Agent 模式会展示 LangGraph 节点执行步骤，例如：
  - `decide_agent_intent`
  - `search_knowledge_base_tool`
  - `validate_context_node`
  - `answer_with_context_tool`
  - `refuse_answer_tool`
- LangGraph Agent 模式如果开启会话保存，会调用 `POST /api/v1/langgraph-agent/conversations/{conversation_id}/chat`，把本轮 user/assistant 消息写入 SQLite。
- 会话保存需要先通过 Conversation API 创建会话，并在页面侧边栏填写对应的 `conversation_id`。
- 保存成功后，页面会显示：
  - `已保存到会话：<conversation_id>`
  - `本轮保存消息数：2`
- 点击示例问题快速体验
- 选择检索模式：
  - `vector`：使用 jieba 分词、词频向量和余弦相似度检索
  - `keyword`：使用 SQLite `LIKE` 关键词检索
  - `embedding`：使用 Ollama `bge-m3` 语义向量检索
  - `precomputed_embedding`：使用已保存的 chunk embedding 检索，适合日常问答
- 调整 `top_k`
- 调整 `min_score`
- 展示本地 Qwen 生成的回答
- 展示检索关键词
- 展开查看引用来源
- 显示回答状态：
  - 已基于知识库引用生成回答
  - 知识库中没有找到相关资料，系统已拒答
  - 本地模型暂时不可用
- 查看当前会话中的对话历史
- 清空对话历史
- 对回答提交简单反馈：
  - 当前反馈会通过 FastAPI 接口 `POST /api/v1/feedback` 保存到 SQLite 数据库，后续可用于统计回答质量。
  - 👍 有帮助
  - 👎 没帮助
- 在侧边栏新增知识文档
- 手动填写标题和正文新增知识文档时，会调用 FastAPI 接口 `POST /api/v1/db/documents/with-content`。
- 根据文档正文自动切分 chunks
- 新增文档后可立即参与 RAG 问答:
  - 新增知识文档时，系统会自动切分 chunks，并使用 Ollama `bge-m3` 为 chunks 生成 embeddings，以便 `precomputed_embedding` 模式检索。
  - 如果文档索引失败，页面会提示确认 Ollama 已启动，并检查 `bge-m3:latest` 模型是否可用。
  - 如果标题、正文或上传文件超过限制，页面会显示更明确的缩短/拆分提示。
  - “注意事项”:
  - 新增知识文档会写入本地 SQLite 数据库 `data/app.db`。该数据库属于运行时数据，已通过 `.gitignore` 忽略，不会提交到 Git。
- 上传 `.txt` 文件并自动读取正文
- txt 上传会调用 FastAPI 后端接口 `POST /api/v1/db/documents/upload-text`，因此使用该功能前需要先启动后端服务。
- 当前 txt 上传要求文件使用 UTF-8 编码；如果编码不兼容，后端会返回上传失败提示。
- 上传文件后可自动使用文件名作为文档标题

### 会话保存

侧边栏中的“会话保存”区域用于把 LangGraph Agent 的本轮问答写入 SQLite。

使用方式：

1. 先调用 `POST /api/v1/conversations` 创建一个会话。
2. 在 Streamlit 页面选择 `LangGraph Agent 问答`。
3. 勾选 `保存 LangGraph Agent 问答到会话`。
4. 填入刚才创建的 `conversation_id`。
5. 提问后，页面会显示保存到哪个会话，以及本轮保存了几条消息。
6. 可以用 `GET /api/v1/conversations/{conversation_id}/messages` 验证消息是否入库。

注意：

- 该功能保存的是本轮 user/assistant 消息。
- 当前还没有把历史消息重新传给 Agent 参与多轮推理。
- 如果填写不存在的 `conversation_id`，后端会返回 `会话不存在。`

### 反馈管理页

启动方式：

```powershell
python -m streamlit run frontend/admin_feedback.py
```

## 文档管理页

启动方式：

```powershell
python -m streamlit run frontend/admin_documents.py
```

该页面用于查看：
  SQLite 文档列表
  指定文档的 chunks 切分结果
说明：该页面更适合作为内部管理/调试页面，用于检查文档是否正确入库，以及正文是否被合理切分。

- 查看每个文档的 embedding 索引状态
- 对比 `chunk_count` 和 `embedding_count`
- 判断文档是否完成 `precomputed_embedding` 检索准备
- 一键补齐缺失的 chunk embeddings
- 补索引会调用 Ollama `bge-m3`，可能需要等待一段时间
