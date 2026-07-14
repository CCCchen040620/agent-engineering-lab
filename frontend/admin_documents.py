import streamlit as st

from backend.config import BACKEND_API_BASE_URL, SQLITE_ADMIN_DATABASE_PATH
from backend.services.sqlite_document_repository import (
    create_chunks_table,
    create_connection,
    create_documents_table,
)
from backend.services.sqlite_embedding_repository import (
    create_chunk_embeddings_table,
    summarize_document_embedding_status,
)
from frontend.api_client import (
    backfill_postgresql_embeddings_api,
    delete_postgresql_document_api,
    get_info_api,
    list_document_chunks_api,
    list_documents_api,
    list_postgresql_document_source_summary_api,
    list_postgresql_document_embedding_status_api,
    rag_backend_supports_feature,
)
from week08.backfill_chunk_embeddings import backfill_chunk_embeddings


SQLITE_BACKEND_LABEL = "SQLite（默认）"
POSTGRESQL_BACKEND_LABEL = "PostgreSQL / pgvector（本地实验）"


def backend_label_to_backend(label: str) -> str:
    if label == POSTGRESQL_BACKEND_LABEL:
        return "postgresql"

    return "sqlite"


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


def load_documents_for_backend(
    backend: str,
    info: dict | None,
    source: str | None = None,
) -> tuple[list[dict], str | None]:
    if not backend_supports(info, backend, "document_listing"):
        return [], "当前后端暂不支持文档列表。"

    documents, error_message = list_documents_api(
        base_url=BACKEND_API_BASE_URL,
        backend=backend,
        source=source,
    )

    if error_message is not None:
        return [], error_message

    return documents or [], None


def load_embedding_statuses() -> list[dict]:
    connection = create_connection(SQLITE_ADMIN_DATABASE_PATH)

    create_documents_table(connection)
    create_chunks_table(connection)
    create_chunk_embeddings_table(connection)

    statuses = summarize_document_embedding_status(connection)

    connection.close()

    return statuses


def load_postgresql_embedding_statuses() -> tuple[list[dict], str | None]:
    statuses, error_message = list_postgresql_document_embedding_status_api(
        base_url=BACKEND_API_BASE_URL,
    )

    if error_message is not None:
        return [], error_message

    return statuses or [], None


def load_postgresql_document_source_summary() -> tuple[list[dict], str | None]:
    summaries, error_message = list_postgresql_document_source_summary_api(
        base_url=BACKEND_API_BASE_URL,
    )

    if error_message is not None:
        return [], error_message

    return summaries or [], None


def render_postgresql_document_source_summary() -> None:
    st.caption("PostgreSQL 文档来源分布")

    summaries, error_message = load_postgresql_document_source_summary()

    if error_message is not None:
        st.error(error_message)
        return

    if summaries == []:
        st.info("暂无 PostgreSQL 文档来源统计。")
        return

    columns = st.columns(len(summaries))

    for index, summary in enumerate(summaries):
        with columns[index]:
            st.metric(
                label=summary["source"],
                value=summary["document_count"],
            )


def render_postgresql_document_delete_form() -> None:
    st.subheader("删除 PostgreSQL 文档")
    st.warning("删除会同时清理该文档的 chunks 和 embeddings，请先确认文档 ID。")

    document_id = st.number_input(
        "要删除的 PostgreSQL 文档 ID",
        min_value=1,
        step=1,
        key="postgresql_delete_document_id",
    )
    confirmed = st.checkbox(
        "我确认要删除这个 PostgreSQL 文档",
        key="postgresql_delete_document_confirmed",
    )

    if st.button(
        "删除 PostgreSQL 文档",
        key="postgresql_delete_document_button",
    ):
        if not confirmed:
            st.warning("请先勾选确认删除。")
            return

        result, error_message = delete_postgresql_document_api(
            base_url=BACKEND_API_BASE_URL,
            document_id=int(document_id),
        )

        if error_message is not None:
            st.error(error_message)
            return

        st.success(f"PostgreSQL 文档已删除：ID {result['id']}")
        st.info("如列表未立即变化，请刷新页面或重新选择筛选条件。")


def render_backend_documents(
    title: str,
    documents: list[dict],
    error_message: str | None,
) -> None:
    st.subheader(title)

    if error_message is not None:
        st.error(error_message)
        return

    if documents == []:
        st.info("暂无文档。")
        return

    st.caption(f"共 {len(documents)} 份文档")
    st.dataframe(documents, use_container_width=True)


def render_document_overview(info: dict | None) -> None:
    st.subheader("文档列表总览")

    sqlite_documents, sqlite_error = load_documents_for_backend(
        backend="sqlite",
        info=info,
    )

    sqlite_column, postgresql_column = st.columns(2)

    with sqlite_column:
        render_backend_documents(
            title="SQLite 文档列表",
            documents=sqlite_documents,
            error_message=sqlite_error,
        )

    with postgresql_column:
        render_postgresql_document_source_summary()

        source_filter_label = st.selectbox(
            "PostgreSQL 来源筛选",
            options=[
                "全部",
                "production",
                "migration",
                "evaluation",
            ],
            key="postgresql_document_source_filter",
        )

        source_filter = None

        if source_filter_label != "全部":
            source_filter = source_filter_label

        postgresql_documents, postgresql_error = load_documents_for_backend(
            backend="postgresql",
            info=info,
            source=source_filter,
        )

        render_backend_documents(
            title=f"PostgreSQL 文档列表（{source_filter_label}）",
            documents=postgresql_documents,
            error_message=postgresql_error,
        )
        render_postgresql_document_delete_form()


def render_sqlite_embedding_status() -> None:
    st.subheader("SQLite Embedding 索引状态")

    embedding_statuses = load_embedding_statuses()

    if embedding_statuses == []:
        st.info("暂无 embedding 索引状态。")
    else:
        st.dataframe(embedding_statuses, use_container_width=True)


def render_postgresql_embedding_status(info: dict | None) -> None:
    st.subheader("PostgreSQL Embedding 索引状态")

    st.caption("需要先启动 postgres，并用 PostgreSQL DATABASE_URL 启动后端。")

    embedding_statuses, error_message = load_postgresql_embedding_statuses()

    if error_message is not None:
        st.error(error_message)
    elif embedding_statuses == []:
        st.info("暂无 embedding 索引状态。")
    else:
        st.dataframe(embedding_statuses, use_container_width=True)

    st.subheader("补齐 PostgreSQL Embedding 索引")

    if not backend_supports(info, "postgresql", "embedding_backfill"):
        st.warning("当前后端暂不支持 PostgreSQL embedding 回填。")
        return

    st.write(
        "这个操作会调用 Ollama / bge-m3，只补齐缺失的 PostgreSQL embeddings，"
        "可能需要等待一段时间。"
    )

    if st.button(
        "补齐 PostgreSQL 缺失 embeddings",
        key="postgresql_embedding_backfill",
    ):
        with st.spinner("正在补齐 PostgreSQL 缺失 embeddings..."):
            result, backfill_error = backfill_postgresql_embeddings_api(
                base_url=BACKEND_API_BASE_URL,
            )

        if backfill_error is not None:
            st.error(backfill_error)
        else:
            st.success("PostgreSQL embedding 回填完成")
            st.write("总 chunks 数量：", result["total_chunks"])
            st.write("更新 embedding 数量：", result["updated"])
            st.write("已存在跳过数量：", result["skipped"])
            st.write("模型：", result["model"])


def render_embedding_status_overview() -> None:
    st.subheader("Embedding 索引状态总览")

    sqlite_column, postgresql_column = st.columns(2)

    with sqlite_column:
        render_sqlite_embedding_status()

    with postgresql_column:
        render_postgresql_embedding_status(info)


def render_sqlite_embedding_backfill() -> None:
    st.subheader("补齐 SQLite Embedding 索引")

    st.write(
        "如果某些 SQLite 文档的 embedding 未完成，可以点击下面按钮补齐缺失索引。"
    )

    if st.button("补齐缺失 embeddings"):
        with st.spinner("正在调用 bge-m3 生成缺失 embeddings..."):
            result = backfill_chunk_embeddings()

        st.success("补索引完成")
        st.write("总 chunks 数量：", result["total_chunks"])
        st.write("新增 embedding 数量：", result["created"])
        st.write("已存在跳过数量：", result["skipped"])


def render_chunks(
    title: str,
    backend: str,
    info: dict | None,
    key_prefix: str,
) -> None:
    st.subheader(title)

    if not backend_supports(info, backend, "chunk_listing"):
        st.warning("当前后端暂不支持查看 chunks。")
        return

    document_id = st.number_input(
        "请输入文档 ID",
        min_value=1,
        step=1,
        key=f"{key_prefix}_document_id",
    )

    if st.button("查看 chunks", key=f"{key_prefix}_view_chunks"):
        chunks, error_message = list_document_chunks_api(
            base_url=BACKEND_API_BASE_URL,
            document_id=int(document_id),
            backend=backend,
        )

        if error_message is not None:
            st.error(error_message)
        elif chunks == []:
            st.warning("没有找到该文档的 chunks。")
        else:
            st.write(f"共 {len(chunks)} 个 chunks")

            for chunk in chunks:
                with st.expander(f"Chunk #{chunk['id']}"):
                    st.write(chunk["text"])


def render_chunks_overview(info: dict | None) -> None:
    st.subheader("查看文档 chunks")

    sqlite_column, postgresql_column = st.columns(2)

    with sqlite_column:
        render_chunks(
            title="SQLite chunks",
            backend="sqlite",
            info=info,
            key_prefix="sqlite_chunks",
        )

    with postgresql_column:
        st.info(
            "PostgreSQL / pgvector chunks 查看需要先启动 postgres，"
            "并用 PostgreSQL DATABASE_URL 启动后端。"
        )
        render_chunks(
            title="PostgreSQL chunks",
            backend="postgresql",
            info=info,
            key_prefix="postgresql_chunks",
        )


st.set_page_config(
    page_title="文档管理",
    page_icon="📫",
    layout="wide",
)

st.title("文档管理")
st.write("同时查看 SQLite 与 PostgreSQL / pgvector 中的文档和切分片段。")

info, info_error = get_info_api(base_url=BACKEND_API_BASE_URL)

if info_error is not None:
    st.warning("暂时无法读取后端能力矩阵，页面将使用默认交互规则。")

render_document_overview(info)

st.divider()
render_chunks_overview(info)

st.divider()
render_embedding_status_overview()

st.divider()
render_sqlite_embedding_backfill()
