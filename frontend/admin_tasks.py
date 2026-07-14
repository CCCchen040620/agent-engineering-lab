import streamlit as st

from frontend.api_client import (
    list_tasks_api,
    run_postgresql_embedding_backfill_task_api,
)
from backend.config import BACKEND_API_BASE_URL


st.set_page_config(page_title="后台任务中心", layout="wide")

st.title("后台任务中心")

st.caption("用于查看后台任务状态，并手动触发 PostgreSQL embedding 回填。")

if st.button("运行 PostgreSQL embedding 回填"):
    try:
        task = run_postgresql_embedding_backfill_task_api(BACKEND_API_BASE_URL)
        if task["status"] == "succeeded":
            st.success("任务执行成功。")
        elif task["status"] == "failed":
            st.error(f"任务执行失败：{task['error']}")
        else:
            st.info(f"任务状态：{task['status']}")

        st.json(task)
    except Exception as error:
        st.error(f"任务请求失败：{error}")

st.divider()

if st.button("刷新任务列表"):
    st.rerun()

try:
    tasks = list_tasks_api(BACKEND_API_BASE_URL)

    if not tasks:
        st.info("暂无任务。")
    else:
        st.dataframe(tasks, use_container_width=True)
except Exception as error:
    st.error(f"无法读取任务列表：{error}")