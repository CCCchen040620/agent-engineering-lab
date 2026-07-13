import streamlit as st

from backend.config import BACKEND_API_BASE_URL
from frontend.document_error_messages import format_document_error_message
from frontend.api_client import (
    chat_with_agent_api,
    chat_with_langgraph_agent_api,
    chat_with_langgraph_agent_conversation_api,
    chat_with_llm_api,
    create_document_with_content_api,
    create_postgresql_document_with_content_api,
    get_conversation_api,
    get_info_api,
    get_system_status_api,
    rag_backend_supports_feature,
    submit_feedback_api,
    upload_text_document_api,
    stream_langgraph_agent_api,
)


st.set_page_config(
    page_title="企业知识库 Agent",
    page_icon="🤖",
    layout="wide",
)

st.title("企业知识库 Agent")
st.write("基于 SQLite 知识库、本地 Ollama/Qwen 和 RAG 的智能问答助手。")

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []


LANGGRAPH_AGENT_ENGINE = "LangGraph Agent 问答"
SQLITE_BACKEND_LABEL = "SQLite（默认）"
POSTGRESQL_BACKEND_LABEL = "PostgreSQL / pgvector（本地实验）"
CHAT_ENGINE_FEATURES = {
    "普通 RAG 问答": "llm_chat",
    "Simple Agent 问答": "simple_agent_chat",
    LANGGRAPH_AGENT_ENGINE: "langgraph_agent_chat",
}


def save_feedback(
    question: str,
    answer: str,
    rating: str,
) -> tuple[dict | None, str | None]:
    return submit_feedback_api(
        base_url=BACKEND_API_BASE_URL,
        question=question,
        answer=answer,
        rating=rating,
    )


def save_document_with_content(
    title: str,
    file_type: str,
    content: str,
) -> tuple[dict | None, str | None]:
    return create_document_with_content_api(
        base_url=BACKEND_API_BASE_URL,
        title=title,
        file_type=file_type,
        content=content,
    )


def save_postgresql_document_with_content(
    title: str,
    file_type: str,
    content: str,
) -> tuple[dict | None, str | None]:
    return create_postgresql_document_with_content_api(
        base_url=BACKEND_API_BASE_URL,
        title=title,
        file_type=file_type,
        content=content,
    )


def backend_supports(
    info: dict | None,
    backend: str,
    feature: str,
) -> bool:
    return rag_backend_supports_feature(
        info=info,
        backend=backend,
        feature=feature,
    )


def backend_label_to_backend(label: str) -> str:
    if label == POSTGRESQL_BACKEND_LABEL:
        return "postgresql"

    return "sqlite"


def format_agent_step(step_index: int, step: dict) -> str:
    tool_name = step.get("tool", step.get("name", "unknown_step"))
    next_action = step.get("next_action", step.get("action", ""))
    observation = step.get("observation", {})

    step_description = f"[{step_index}] {tool_name}"

    if next_action != "":
        step_description = step_description + f" -> {next_action}"

    if "result_count" in observation:
        step_description = (
            step_description
            + f" | 命中数量：{observation['result_count']}"
        )

    if "document_count" in observation:
        step_description = (
            step_description
            + f" | 文档数量：{observation['document_count']}"
        )

    if "citation_count" in observation:
        step_description = (
            step_description
            + f" | 引用数量：{observation['citation_count']}"
        )

    return step_description


def render_status_line(label: str, is_ok: bool) -> None:
    if is_ok:
        st.success(f"{label}：正常")
    else:
        st.error(f"{label}：异常")


def render_system_status() -> None:
    status, error_message = get_system_status_api(
        base_url=BACKEND_API_BASE_URL,
    )

    with st.expander("系统状态诊断", expanded=True):
        if error_message is not None:
            st.error(error_message)
            return

        render_status_line("API", status["api"] == "ok")

        database_status = status["database"]
        database_url = database_status.get("database_url", "")

        if database_url.startswith("postgresql://"):
            database_label = "当前数据库：PostgreSQL"
        else:
            database_label = "当前数据库：SQLite"

        render_status_line(database_label, database_status["status"] == "ok")

        postgresql_status = status.get("postgresql", {})

        if postgresql_status.get("enabled") is True:
            render_status_line(
                "PostgreSQL / pgvector",
                postgresql_status.get("status") == "ok",
            )
        else:
            st.caption("PostgreSQL / pgvector：当前未启用")

        render_status_line("Ollama", status["ollama"]["status"] == "ok")

        llm_model = status["ollama"]["llm_model"]
        embedding_model = status["ollama"]["embedding_model"]

        render_status_line(
            f"LLM：{llm_model['name']}",
            llm_model["available"],
        )
        render_status_line(
            f"Embedding：{embedding_model['name']}",
            embedding_model["available"],
        )


with st.sidebar:
    render_system_status()

    info, info_error = get_info_api(base_url=BACKEND_API_BASE_URL)

    if info_error is not None:
        st.caption("暂时无法读取后端能力矩阵，前端将使用默认交互规则。")

    st.divider()
    st.header("检索设置")

    chat_engine = st.radio(
        "问答引擎",
        ["普通 RAG 问答", "Simple Agent 问答", "LangGraph Agent 问答"],
        index=0,
    )

    retriever_backend_label = st.radio(
    "检索后端",
    [SQLITE_BACKEND_LABEL, POSTGRESQL_BACKEND_LABEL],
    index=0,
    )

    retriever_backend = backend_label_to_backend(retriever_backend_label)

    if retriever_backend == "postgresql":
        st.info(
            "PostgreSQL / pgvector 模式需要先启动 postgres，并用 PostgreSQL DATABASE_URL 启动后端。"
        )

    chat_engine_feature = CHAT_ENGINE_FEATURES[chat_engine]

    if not backend_supports(info, retriever_backend, chat_engine_feature):
        st.info(
            f"{retriever_backend_label} 当前不支持 {chat_engine}，"
            f"已自动切换为 {LANGGRAPH_AGENT_ENGINE}。"
        )
        chat_engine = LANGGRAPH_AGENT_ENGINE

    mode = st.radio(
        "检索模式",
        ["precomputed_embedding", "embedding", "vector", "keyword"],
        index=0,
    )

    top_k = st.slider(
        "最多引用片段 top_k",
        min_value=1,
        max_value=5,
        value=3,
    )

    min_score = st.slider(
        "最低相似度 min_score",
        min_value=0.0,
        max_value=1.0,
        value=0.3,
        step=0.05,
    )

    timeout_seconds = st.slider(
        "Agent 超时时间 timeout_seconds",
        min_value=1,
        max_value=120,
        value=30,
    )

    use_streaming = st.checkbox(
        "使用学习版流式输出",
        value=False,
    )

    st.divider()
    st.header("会话保存")

    save_to_conversation = st.checkbox(
        "保存 LangGraph Agent 问答到会话",
        value=False,
    )

    if use_streaming and not backend_supports(
        info,
        retriever_backend,
        "streaming_chat",
    ):
        st.info(
            f"{retriever_backend_label} 当前不支持流式输出，已自动关闭。"
        )
        use_streaming = False

    if save_to_conversation and not backend_supports(
        info,
        retriever_backend,
        "conversation_chat",
    ):
        st.info(
            f"{retriever_backend_label} 当前不支持会话保存，已自动关闭。"
        )
        save_to_conversation = False

    conversation_id = st.number_input(
        "conversation_id",
        min_value=1,
        value=1,
        step=1,
    )

    if save_to_conversation:
        conversation, conversation_error = get_conversation_api(
            base_url=BACKEND_API_BASE_URL,
            conversation_id=int(conversation_id),
        )

        if conversation_error is not None:
            st.warning(f"无法读取当前会话：{conversation_error}")
        else:
            st.caption(f"当前会话：{conversation['title']}")

            if conversation["summary"] == "":
                st.info("当前会话还没有摘要。")
            else:
                st.info(f"当前会话摘要：{conversation['summary']}")

    if st.button("清空对话历史"):
        st.session_state["chat_history"] = []

    st.divider()
    st.header("新增知识文档")

    document_storage_backend = st.selectbox(
        "入库后端",
        [SQLITE_BACKEND_LABEL, POSTGRESQL_BACKEND_LABEL],
    )
    document_storage_backend_name = backend_label_to_backend(document_storage_backend)

    if document_storage_backend_name == "postgresql":
        st.info(
            "PostgreSQL / pgvector 入库需要后端使用 PostgreSQL DATABASE_URL 启动，"
            "并确保 Ollama 和 bge-m3 可用。"
        )

    document_title = st.text_input("文档标题")
    document_file_type = st.selectbox("文件类型", ["md", "txt", "pdf"])
    document_content = st.text_area("文档正文", height=160)

    uploaded_file = st.file_uploader(
        "上传 txt 文件",
        type=["txt"],
    )

    if uploaded_file is not None:
        if document_title.strip() == "":
            document_title = uploaded_file.name.rsplit(".", 1)[0]

        document_file_type = "txt"

        st.info(f"已准备上传文件：{uploaded_file.name}")

    if st.button("新增并索引"):
        if uploaded_file is not None:
            if not backend_supports(
                info,
                document_storage_backend_name,
                "txt_file_upload",
            ):
                st.warning(
                    f"{document_storage_backend} 当前不支持 txt 文件上传，"
                    "请把文本粘贴到“文档正文”后再新增。"
                )
            else:
                with st.spinner("正在通过后端上传 txt 文档并生成 embeddings..."):
                    document, error_message = upload_text_document_api(
                        base_url=BACKEND_API_BASE_URL,
                        file_name=uploaded_file.name,
                        content=uploaded_file.getvalue(),
                        title=document_title.strip(),
                )

                if error_message is not None:
                    st.error(format_document_error_message(error_message))
                else:
                    st.success(
                        f"已新增文档：{document['title']}，切分片段数：{document['chunk_count']}"
                    )
        elif document_title.strip() == "" or document_content.strip() == "":
            st.warning("文档标题和正文不能为空。")
        else:
            if not backend_supports(
                info,
                document_storage_backend_name,
                "document_content_indexing",
            ):
                st.warning(
                    f"{document_storage_backend} 当前不支持粘贴正文入库。"
                )
            elif document_storage_backend_name == "postgresql":
                with st.spinner(
                    "正在写入 PostgreSQL、切分 chunks 并生成 pgvector embeddings..."
                ):
                    document, error_message = save_postgresql_document_with_content(
                        title=document_title.strip(),
                        file_type=document_file_type,
                        content=document_content.strip(),
                    )
            else:
                with st.spinner("正在新增文档、切分 chunks 并生成 embeddings..."):
                    document, error_message = save_document_with_content(
                        title=document_title.strip(),
                        file_type=document_file_type,
                        content=document_content.strip(),
                    )

            if error_message is not None:
                st.error(format_document_error_message(error_message))
            else:
                st.success(
                    f"已新增文档：{document['title']}，切分片段数：{document['chunk_count']}"
                )

st.subheader("示例问题")

example_questions = [
    "新员工什么时候完成安全培训？",
    "员工每天需要工作多久？",
    "请假需要怎么申请？",
    "公司有没有股票期权？",
]

columns = st.columns(len(example_questions))

for column, example_question in zip(columns, example_questions):
    if column.button(example_question):
        st.session_state["question"] = example_question

question = st.text_input(
    "请输入你的问题",
    placeholder="例如：新员工什么时候完成安全培训？",
    key="question",
)

if st.button("提问"):
    if question.strip() == "":
        st.warning("请输入问题后再提问。")
    else:
        answer_rendered_during_streaming = False

        with st.spinner("正在检索知识库并调用本地 Qwen 生成回答..."):
            if chat_engine == "Simple Agent 问答":
                response, error_message = chat_with_agent_api(
                    base_url=BACKEND_API_BASE_URL,
                    question=question.strip(),
                    top_k=top_k,
                    mode=mode,
                    min_score=min_score,
                )
            elif chat_engine == "LangGraph Agent 问答":
                if use_streaming and save_to_conversation:
                    st.info("学习版流式输出暂不支持会话保存，已自动使用普通 LangGraph Agent 问答。")

                if use_streaming and not save_to_conversation:
                    st.subheader("回答")
                    answer_placeholder = st.empty()
                    streamed_answer = ""
                    metadata = {}
                    error_message = None
                    answer_rendered_during_streaming = True

                    for event in stream_langgraph_agent_api(
                        base_url=BACKEND_API_BASE_URL,
                        question=question.strip(),
                        top_k=top_k,
                        mode=mode,
                        min_score=min_score,
                        timeout_seconds=timeout_seconds,
                    ):
                        if event["type"] == "delta":
                            streamed_answer = streamed_answer + event["content"]
                            answer_placeholder.write(streamed_answer)

                        elif event["type"] == "metadata":
                            metadata = event

                        elif event["type"] == "error":
                            error_message = event["message"]

                        elif event["type"] == "done":
                            break

                    if error_message is not None:
                        response = None
                    else:
                        response = {
                            "question": question.strip(),
                            "keyword": metadata.get("keyword", ""),
                            "answer": streamed_answer,
                            "citations": [],
                            "steps": [],
                            "is_fallback": metadata.get("is_fallback", False),
                            "is_timeout": metadata.get("is_timeout", False),
                        }
                else:
                    if save_to_conversation:
                        response, error_message = chat_with_langgraph_agent_conversation_api(
                            base_url=BACKEND_API_BASE_URL,
                            conversation_id=int(conversation_id),
                            question=question.strip(),
                            top_k=top_k,
                            mode=mode,
                            min_score=min_score,
                            timeout_seconds=timeout_seconds,
                        )
                    else:
                        response, error_message = chat_with_langgraph_agent_api(
                            base_url=BACKEND_API_BASE_URL,
                            question=question.strip(),
                            top_k=top_k,
                            mode=mode,
                            min_score=min_score,
                            timeout_seconds=timeout_seconds,
                            retriever_backend=retriever_backend,
                        )
            else:
                response, error_message = chat_with_llm_api(
                    base_url=BACKEND_API_BASE_URL,
                    question=question.strip(),
                    top_k=top_k,
                    mode=mode,
                    min_score=min_score,
                )

        if error_message is not None:
            st.error(error_message)
        else:
            history_item = response.copy()
            history_item["engine"] = chat_engine
            history_item["retriever_backend"] = retriever_backend
            history_item["feedback"] = None
            history_item["feedback_id"] = None
            st.session_state["chat_history"].append(history_item)

            if not answer_rendered_during_streaming:
                st.subheader("回答")

            if response.get("is_fallback") is True:
                st.warning("本地模型不可用，已使用知识库片段生成基础回答。")
            elif "本地模型暂时不可用" in response["answer"]:
                st.warning("本地模型暂时不可用，请稍后再试。")
            elif "暂时无法回答" in response["answer"]:
                st.warning("知识库中没有找到相关资料，系统已拒答。")
            elif len(response["citations"]) > 0:
                st.success("已基于知识库引用生成回答。")
            else:
                st.info("已生成回答，但本次没有引用来源。")

            if not answer_rendered_during_streaming:
                st.write(response["answer"])

            st.caption(f"检索关键词：{response['keyword']}")
            st.caption(f"问答引擎：{chat_engine}")
            st.caption(f"检索后端：{retriever_backend}")

            if "conversation_id" in response:
                st.caption(f"已保存到会话：{response['conversation_id']}")

            if "saved_messages" in response:
                st.caption(f"本轮保存消息数：{len(response['saved_messages'])}")

            if "steps" in response:
                st.subheader("Agent 执行步骤")

                for step_index, step in enumerate(response["steps"], start=1):
                    st.markdown(f"- {format_agent_step(step_index, step)}")

            st.subheader("引用来源")

            if response["citations"] == []:
                st.info("本次回答没有引用来源。")
            else:
                for index, citation in enumerate(response["citations"], start=1):
                    with st.expander(f"[{index}] {citation['title']}"):
                        st.write(citation["text"])
                        st.caption(citation["path"])

if st.session_state["chat_history"] != []:
    st.subheader("对话历史")

    for index, item in reversed(
        list(enumerate(st.session_state["chat_history"]))
    ):
        with st.expander(item["question"]):
            st.write(item["answer"])
            caption_text = (
                f"引擎：{item.get('engine', '普通 RAG 问答')} "
                f"| 检索后端：{item.get('retriever_backend', 'sqlite')} "
                f"| 关键词：{item['keyword']} "
                f"| 引用数量：{len(item['citations'])}"
            )

            if item.get("is_fallback") is True:
                caption_text = caption_text + " | 降级回答"

            if "conversation_id" in item:
                caption_text = caption_text + f" | 会话：{item['conversation_id']}"

            st.caption(caption_text)

            if "steps" in item:
                st.markdown("Agent 执行步骤：")

            for step_index, step in enumerate(item["steps"], start=1):
                st.markdown(f"- {format_agent_step(step_index, step)}")

            feedback_columns = st.columns(2)

            if feedback_columns[0].button(
                "👍 有帮助",
                key=f"helpful_{index}",
            ):
                feedback, error_message = save_feedback(
                    question=item["question"],
                    answer=item["answer"],
                    rating="helpful",
                )

                if error_message is not None:
                    st.error(error_message)
                else:
                    st.session_state["chat_history"][index]["feedback"] = "有帮助"
                    st.session_state["chat_history"][index]["feedback_id"] = feedback[
                        "id"
                    ]

            if feedback_columns[1].button(
                "👎 没帮助",
                key=f"not_helpful_{index}",
            ):
                feedback, error_message = save_feedback(
                    question=item["question"],
                    answer=item["answer"],
                    rating="not_helpful",
                )

                if error_message is not None:
                    st.error(error_message)
                else:
                    st.session_state["chat_history"][index]["feedback"] = "没帮助"
                    st.session_state["chat_history"][index]["feedback_id"] = feedback[
                        "id"
                    ]

            if item["feedback"] is not None:
                st.caption(
                    f"反馈：{item['feedback']} | 反馈编号：{item['feedback_id']}"
                )

            if item["citations"] != []:
                for citation_index, citation in enumerate(item["citations"], start=1):
                    st.markdown(
                        f"- [{citation_index}] {citation['title']}：{citation['text']}"
                    )
