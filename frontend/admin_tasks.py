import streamlit as st

from frontend.api_client import (
    cancel_task_api,
    create_task_api,
    get_info_api,
    get_task_api,
    list_tasks_api,
    retry_task_async_api,
    run_postgresql_embedding_backfill_task_api,
    run_task_async_api,
)
from frontend.task_result_summary import (
    build_task_result_summary,
)
from frontend.task_failure_view import build_task_failure_summary
from frontend.task_progress_view import (
    build_task_progress_text,
    clamp_progress_percent,
)
from frontend.task_list_view import (
    TASK_STATUS_FILTER_OPTIONS,
    build_task_attempt_summary_text,
    build_task_retry_source_text,
    build_task_list_rows,
)
from frontend.task_storage_view import build_task_storage_caption
from backend.config import BACKEND_API_BASE_URL


POSTGRESQL_EMBEDDING_BACKFILL_TASK_TYPE = "postgresql_embedding_backfill"


def render_task_attempt_summary(task: dict) -> None:
    st.caption(f"运行统计：{build_task_attempt_summary_text(task)}")


def render_task_failure_summary(task: dict) -> None:
    failure_items = build_task_failure_summary(task)

    if not failure_items:
        return

    st.subheader("失败诊断")

    for item in failure_items:
        st.write(f"{item['label']}：{item['value']}")


def render_task_progress(task: dict) -> None:
    progress_text = build_task_progress_text(task)

    if progress_text == "":
        return

    progress_percent = task.get("progress_percent")

    if progress_percent is not None:
        st.progress(clamp_progress_percent(int(progress_percent)))

    st.caption(f"任务进度：{progress_text}")


def render_task_retry_source(task: dict) -> None:
    retry_source_text = build_task_retry_source_text(task)

    if retry_source_text == "":
        return

    st.caption(f"重试来源：{retry_source_text}")


st.set_page_config(page_title="后台任务中心", layout="wide")

st.title("后台任务中心")

st.caption("用于查看后台任务状态，并手动触发 PostgreSQL embedding 回填。")

info, info_error = get_info_api(BACKEND_API_BASE_URL)

if info_error is None:
    st.info(build_task_storage_caption(info))
else:
    st.warning("暂时无法读取任务存储后端，请确认 FastAPI 已启动。")

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

        render_task_progress(task)
        render_task_retry_source(task)
        render_task_attempt_summary(task)

        summary_items = build_task_result_summary(task)

        if summary_items:
            st.subheader("任务结果摘要")
            columns = st.columns(len(summary_items))

            for column, item in zip(columns, summary_items):
                column.metric(item["label"], item["value"])

        render_task_failure_summary(task)

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

view_column, retry_column, cancel_column = st.columns(3)

with view_column:
    view_task_detail = st.button("查看任务详情")

with retry_column:
    retry_failed_task = st.button("重试失败任务（异步）")

with cancel_column:
    cancel_pending_task = st.button("取消等待任务")

if view_task_detail:
    try:
        task = get_task_api(BACKEND_API_BASE_URL, int(task_id_to_view))
        st.write(f"任务状态：`{task['status']}`")

        render_task_progress(task)
        render_task_retry_source(task)
        render_task_attempt_summary(task)

        summary_items = build_task_result_summary(task)

        if summary_items:
            st.subheader("任务结果摘要")
            columns = st.columns(len(summary_items))

            for column, item in zip(columns, summary_items):
                column.metric(item["label"], item["value"])

        render_task_failure_summary(task)

        st.json(task)
    except Exception as error:
        st.error(f"无法读取任务详情：{error}")

if retry_failed_task:
    try:
        retry_task = retry_task_async_api(BACKEND_API_BASE_URL, int(task_id_to_view))
        st.success(
            f"已创建重试任务，任务 ID：{retry_task['id']}。"
            "请刷新任务列表查看执行结果。"
        )
        render_task_progress(retry_task)
        render_task_retry_source(retry_task)
        render_task_attempt_summary(retry_task)
        st.json(retry_task)
    except Exception as error:
        st.error(f"无法重试任务：{error}")

if cancel_pending_task:
    try:
        canceled_task = cancel_task_api(BACKEND_API_BASE_URL, int(task_id_to_view))
        st.success(f"任务已取消，任务 ID：{canceled_task['id']}。")
        render_task_progress(canceled_task)
        render_task_retry_source(canceled_task)
        render_task_attempt_summary(canceled_task)
        st.json(canceled_task)
    except Exception as error:
        st.error(f"无法取消任务：{error}")

st.divider()

st.subheader("任务列表")
st.caption("默认按最新任务优先显示；异步任务提交后，点击“刷新列表”查看最新状态。")

filter_column, sort_column, limit_column, refresh_column = st.columns([2, 2, 2, 1])

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

with limit_column:
    limit_option = st.selectbox(
        "最多显示任务数",
        ["20", "50", "100", "全部"],
    )

with refresh_column:
    st.write("")
    st.write("")

    if st.button("刷新列表"):
        st.rerun()

task_limit = None if limit_option == "全部" else int(limit_option)

try:
    tasks = list_tasks_api(
        BACKEND_API_BASE_URL,
        status=status_filter,
        order="desc" if newest_first else "asc",
        limit=task_limit,
    )

    if not tasks:
        st.info("暂无任务。")
    else:
        display_tasks = build_task_list_rows(
            tasks,
            status_filter="全部",
            newest_first=newest_first,
        )

        st.caption(f"当前显示 {len(display_tasks)} 个任务。")

        if not display_tasks:
            st.info("当前筛选条件下没有任务。")
        else:
            st.dataframe(display_tasks, use_container_width=True)
except Exception as error:
    st.error(f"无法读取任务列表：{error}")
