import streamlit as st

from backend.services.sqlite_document_repository import create_connection
from backend.services.sqlite_feedback_repository import (
    create_feedback_table,
    list_feedback_from_db,
    summarize_feedback_from_db,
)
from week04.settings import SQLITE_DATABASE_PATH


def load_feedback_data() -> tuple[list[dict], dict]:
    connection = create_connection(SQLITE_DATABASE_PATH)

    create_feedback_table(connection)

    feedback_items = list_feedback_from_db(connection)
    summary = summarize_feedback_from_db(connection)

    connection.close()

    return feedback_items, summary


st.set_page_config(
    page_title="反馈管理",
    page_icon="📊",
    layout="wide",
)

st.title("反馈管理")
st.write("查看企业知识库 Agent 的用户反馈数据。")

feedback_items, summary = load_feedback_data()

st.subheader("反馈统计")

first_column, second_column, third_column = st.columns(3)

first_column.metric("总反馈", summary["total"])
second_column.metric("有帮助", summary["helpful"])
third_column.metric("没帮助", summary["not_helpful"])

st.subheader("反馈列表")

if feedback_items == []:
    st.info("暂无反馈数据。")
else:
    for feedback in reversed(feedback_items):
        with st.expander(f"#{feedback['id']} - {feedback['rating']}"):
            st.write("问题：")
            st.write(feedback["question"])

            st.write("回答：")
            st.write(feedback["answer"])

            st.caption(f"反馈：{feedback['rating']}")