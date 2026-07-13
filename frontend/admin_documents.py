import streamlit as st

from backend.config import BACKEND_API_BASE_URL
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
    get_info_api,
    list_document_chunks_api,
    list_documents_api,
    rag_backend_supports_feature,
)
from week04.settings import SQLITE_DATABASE_PATH
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


def load_embedding_statuses() -> list[dict]:
    connection = create_connection(SQLITE_DATABASE_PATH)

    create_documents_table(connection)
    create_chunks_table(connection)
    create_chunk_embeddings_table(connection)

    statuses = summarize_document_embedding_status(connection)

    connection.close()

    return statuses


def render_sqlite_embedding_tools() -> None:
    embedding_statuses = load_embedding_statuses()

    st.subheader("Embedding 索引状态")

    if embedding_statuses == []:
        st.info("暂无 embedding 索引状态。")
    else:
        st.dataframe(embedding_statuses, use_container_width=True)

    st.subheader("补齐 Embedding 索引")

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


def render_documents(documents: list[dict]) -> None:
    st.subheader("文档列表")

    if documents == []:
        st.info("暂无文档。")
    else:
        st.dataframe(documents, use_container_width=True)


def render_chunks(
    backend: str,
    info: dict | None,
) -> None:
    st.subheader("查看文档 chunks")

    if not backend_supports(info, backend, "chunk_listing"):
        st.warning("当前后端暂不支持查看 chunks。")
        return

    document_id = st.number_input(
        "请输入文档 ID",
        min_value=1,
        step=1,
    )

    if st.button("查看 chunks"):
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


st.set_page_config(
    page_title="文档管理",
    page_icon="📫",
    layout="wide",
)

st.title("文档管理")
st.write("查看企业知识库中的文档和切分片段。")

info, info_error = get_info_api(base_url=BACKEND_API_BASE_URL)

if info_error is not None:
    st.warning("暂时无法读取后端能力矩阵，页面将使用默认交互规则。")

backend_label = st.radio(
    "文档后端",
    [SQLITE_BACKEND_LABEL, POSTGRESQL_BACKEND_LABEL],
    index=0,
)
backend = backend_label_to_backend(backend_label)

if backend == "postgresql":
    st.info(
        "PostgreSQL / pgvector 文档管理需要先启动 postgres，"
        "并用 PostgreSQL DATABASE_URL 启动后端。"
    )

if backend_supports(info, backend, "document_listing"):
    documents, error_message = list_documents_api(
        base_url=BACKEND_API_BASE_URL,
        backend=backend,
    )

    if error_message is not None:
        st.error(error_message)
        documents = []
else:
    st.warning("当前后端暂不支持文档列表。")
    documents = []

render_documents(documents)

if backend == "sqlite":
    render_sqlite_embedding_tools()
else:
    st.info("PostgreSQL 的 embedding 状态和补齐操作后续再接入管理页。")

render_chunks(backend=backend, info=info)
