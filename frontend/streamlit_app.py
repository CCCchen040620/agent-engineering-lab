import streamlit as st

from backend.services.sqlite_llm_qa_service import build_sqlite_llm_chat_response


st.set_page_config(
    page_title="企业知识库 Agent",
    page_icon="🤖",
    layout="wide",
)

st.title("企业知识库 Agent")
st.write("基于 SQLite 知识库、本地 Ollama/Qwen 和 RAG 的智能问答助手。")

with st.sidebar:
    st.header("检索设置")

    mode = st.radio(
        "检索模式",
        ["vector", "keyword"],
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
            response = build_sqlite_llm_chat_response(
                question.strip(),
                top_k=top_k,
                mode=mode,
                min_score=min_score,
            )

        st.subheader("回答")
        st.write(response.answer)

        st.caption(f"检索关键词：{response.keyword}")

        st.subheader("引用来源")

        if response.citations == []:
            st.info("本次回答没有引用来源。")
        else:
            for index, citation in enumerate(response.citations, start=1):
                with st.expander(f"[{index}] {citation.title}"):
                    st.write(citation.text)
                    st.caption(citation.path)