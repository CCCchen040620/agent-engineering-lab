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

## 页面功能

当前页面支持：

- 输入企业知识库问题
- 提问时会调用 FastAPI 后端接口 `POST /api/v1/db/chat/llm`，由后端完成检索、组装提示词和调用本地大模型。
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
- 根据文档正文自动切分 chunks
- 新增文档后可立即参与 RAG 问答:
  - 新增知识文档时，系统会自动切分 chunks，并使用 Ollama `bge-m3` 为 chunks 生成 embeddings，以便 `precomputed_embedding` 模式检索。
  - “注意事项”:
  - 新增知识文档会写入本地 SQLite 数据库 `data/app.db`。该数据库属于运行时数据，已通过 `.gitignore` 忽略，不会提交到 Git。
- 上传 `.txt` 文件并自动读取正文
- txt 上传会调用 FastAPI 后端接口 `POST /api/v1/db/documents/upload-text`，因此使用该功能前需要先启动后端服务。
- 当前 txt 上传要求文件使用 UTF-8 编码；如果编码不兼容，后端会返回上传失败提示。
- 上传文件后可自动使用文件名作为文档标题

### 反馈管理页

启动方式：

python -m streamlit run frontend/admin_feedback.py

## 文档管理页

启动方式：

```powershell
python -m streamlit run frontend/admin_documents.py

该页面用于查看：
  SQLite 文档列表
  指定文档的 chunks 切分结果
说明：该页面更适合作为内部管理/调试页面，用于检查文档是否正确入库，以及正文是否被合理切分。

- 查看每个文档的 embedding 索引状态
- 对比 `chunk_count` 和 `embedding_count`
- 判断文档是否完成 `precomputed_embedding` 检索准备
- 一键补齐缺失的 chunk embeddings
- 补索引会调用 Ollama `bge-m3`，可能需要等待一段时间
