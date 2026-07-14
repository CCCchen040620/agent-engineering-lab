import streamlit as st

from frontend.api_client import (
    create_task_api,
    get_task_api,
    list_tasks_api,
    run_postgresql_embedding_backfill_task_api,
    run_task_async_api,
)
from frontend.task_result_summary import (
    build_task_result_summary,
)
from frontend.task_list_view import (
    TASK_STATUS_FILTER_OPTIONS,
    build_task_list_rows,
)
from backend.config import BACKEND_API_BASE_URL


POSTGRESQL_EMBEDDING_BACKFILL_TASK_TYPE = "postgresql_embedding_backfill"


st.set_page_config(page_title="后台任务中心", layout="wide")

st.title("后台任务中心")

st.caption("用于查看后台任务状态，并手动触发 PostgreSQL embedding 回填。")

run_mode = st.radio(
    "运行方式",
    ["同步运行（等待完成）", "异步运行（立即返回）"],
    horizontal=True,
)

if st.button("运行 PostgreSQL embedding 回填"):
    try:
        if run_mode == "同步运行（等待完成）":
            task = run_postgresql_embedding_backfill_task_api(BACKEND_API_BASE_URL)
        else:
            created_task = create_task_api(
                BACKEND_API_BASE_URL,
                task_type=POSTGRESQL_EMBEDDING_BACKFILL_TASK_TYPE,
                payload={},
            )
            task = run_task_async_api(BACKEND_API_BASE_URL, created_task["id"])

        if task["status"] == "succeeded":
            st.success("任务执行成功。")
        elif task["status"] == "running":
            st.info(f"任务已开始，任务 ID：{task['id']}。请刷新任务列表查看结果。")
        elif task["status"] == "failed":
            st.error(f"任务执行失败：{task['error']}")
        else:
            st.info(f"任务状态：{task['status']}")

        summary_items = build_task_result_summary(task)

        if summary_items:
            st.subheader("任务结果摘要")
            columns = st.columns(len(summary_items))

            for column, item in zip(columns, summary_items):
                column.metric(item["label"], item["value"])

        st.json(task)
    except Exception as error:
        st.error(f"任务请求失败：{error}")

st.divider()

st.subheader("查看单个任务详情")

task_id_to_view = st.number_input(
    "任务 ID",
    min_value=1,
    step=1,
    value=1,
)

if st.button("查看任务详情"):
    try:
        task = get_task_api(BACKEND_API_BASE_URL, int(task_id_to_view))
        st.write(f"任务状态：`{task['status']}`")

        summary_items = build_task_result_summary(task)

        if summary_items:
            st.subheader("任务结果摘要")
            columns = st.columns(len(summary_items))

            for column, item in zip(columns, summary_items):
                column.metric(item["label"], item["value"])

        st.json(task)
    except Exception as error:
        st.error(f"无法读取任务详情：{error}")

st.divider()

st.subheader("任务列表")

filter_column, sort_column, refresh_column = st.columns([2, 2, 1])

with filter_column:
    status_filter = st.selectbox(
        "任务状态筛选",
        TASK_STATUS_FILTER_OPTIONS,
    )

with sort_column:
    newest_first = st.checkbox(
        "最新任务优先",
        value=True,
    )

with refresh_column:
    st.write("")
    st.write("")

    if st.button("刷新列表"):
        st.rerun()

try:
    tasks = list_tasks_api(
        BACKEND_API_BASE_URL,
        status=status_filter,
    )

    if not tasks:
        st.info("暂无任务。")
    else:
        display_tasks = build_task_list_rows(
            tasks,
            status_filter="全部",
            newest_first=newest_first,
        )

        st.caption(f"当前显示 {len(display_tasks)} / {len(tasks)} 个任务。")

        if not display_tasks:
            st.info("当前筛选条件下没有任务。")
        else:
            st.dataframe(display_tasks, use_container_width=True)
except Exception as error:
    st.error(f"无法读取任务列表：{error}")
