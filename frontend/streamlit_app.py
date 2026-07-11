import streamlit as st

from backend.config import BACKEND_API_BASE_URL
from frontend.document_error_messages import format_document_error_message
from frontend.api_client import (
    chat_with_agent_api,
    chat_with_langgraph_agent_api,
    chat_with_langgraph_agent_conversation_api,
    chat_with_llm_api,
    create_document_with_content_api,
    get_conversation_api,
    get_system_status_api,
    submit_feedback_api,
    upload_text_document_api,
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
        render_status_line("SQLite", status["database"]["status"] == "ok")
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

    st.divider()
    st.header("检索设置")

    chat_engine = st.radio(
        "问答引擎",
        ["普通 RAG 问答", "Simple Agent 问答", "LangGraph Agent 问答"],
        index=0,
    )

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

    st.divider()
    st.header("会话保存")

    save_to_conversation = st.checkbox(
        "保存 LangGraph Agent 问答到会话",
        value=False,
    )

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
            history_item["feedback"] = None
            history_item["feedback_id"] = None
            st.session_state["chat_history"].append(history_item)

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

            st.write(response["answer"])

            st.caption(f"检索关键词：{response['keyword']}")
            st.caption(f"问答引擎：{chat_engine}")

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
