import requests
import streamlit as st

from backend.config import BACKEND_API_BASE_URL
from backend.services.document_indexing_service import (
    create_document_with_chunks_and_embeddings,
)
from backend.services.sqlite_document_repository import create_connection
from frontend.api_client import chat_with_llm_api, submit_feedback_api
from week04.settings import SQLITE_DATABASE_PATH


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


def save_document_with_content(title: str, file_type: str, content: str) -> dict | None:
    connection = create_connection(SQLITE_DATABASE_PATH)

    document = create_document_with_chunks_and_embeddings(
        connection,
        title=title,
        file_type=file_type,
        content=content,
    )

    connection.close()

    return document


def upload_text_document_to_api(
    file_name: str,
    content: bytes,
    title: str,
) -> tuple[dict | None, str | None]:
    data = {}

    if title != "":
        data["title"] = title

    try:
        response = requests.post(
            BACKEND_API_BASE_URL + "/api/v1/db/documents/upload-text",
            data=data,
            files={
                "file": (
                    file_name,
                    content,
                    "text/plain",
                )
            },
            timeout=300,
        )
    except requests.RequestException:
        return None, "后端服务暂时不可用，请确认 FastAPI 已启动。"

    if response.status_code == 201:
        return response.json(), None

    try:
        detail = response.json()["detail"]
    except Exception:
        detail = "上传失败，请稍后再试。"

    return None, detail


with st.sidebar:
    st.header("检索设置")

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
                document, error_message = upload_text_document_to_api(
                    file_name=uploaded_file.name,
                    content=uploaded_file.getvalue(),
                    title=document_title.strip(),
                )

            if error_message is not None:
                st.error(error_message)
            else:
                st.success(
                    f"已新增文档：{document['title']}，切分片段数：{document['chunk_count']}"
                )
        elif document_title.strip() == "" or document_content.strip() == "":
            st.warning("文档标题和正文不能为空。")
        else:
            with st.spinner("正在新增文档、切分 chunks 并生成 embeddings..."):
                document = save_document_with_content(
                    title=document_title.strip(),
                    file_type=document_file_type,
                    content=document_content.strip(),
                )

            if document is None:
                st.error("文档标题已存在，无法重复新增。")
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
            history_item["feedback"] = None
            history_item["feedback_id"] = None
            st.session_state["chat_history"].append(history_item)

            st.subheader("回答")

            if "本地模型暂时不可用" in response["answer"]:
                st.warning("本地模型暂时不可用，请稍后再试。")
            elif "暂时无法回答" in response["answer"]:
                st.warning("知识库中没有找到相关资料，系统已拒答。")
            elif len(response["citations"]) > 0:
                st.success("已基于知识库引用生成回答。")
            else:
                st.info("已生成回答，但本次没有引用来源。")

            st.write(response["answer"])

            st.caption(f"检索关键词：{response['keyword']}")

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
            st.caption(
                f"关键词：{item['keyword']} | 引用数量：{len(item['citations'])}"
            )

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
