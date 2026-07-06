import streamlit as st

from week08.backfill_chunk_embeddings import backfill_chunk_embeddings
from backend.services.sqlite_document_repository import (
    create_chunks_table,
    create_connection,
    create_documents_table,
    list_chunks_by_document_id,
    list_documents_from_db,
)
from backend.services.sqlite_embedding_repository import (
    create_chunk_embeddings_table,
    summarize_document_embedding_status,
)
from week04.settings import SQLITE_DATABASE_PATH


def load_documents() -> list[dict]:
    connection = create_connection(SQLITE_DATABASE_PATH)

    create_documents_table(connection)

    documents = list_documents_from_db(connection)

    connection.close()

    return documents


def load_embedding_statuses() -> list[dict]:
    connection = create_connection(SQLITE_DATABASE_PATH)

    create_documents_table(connection)
    create_chunks_table(connection)
    create_chunk_embeddings_table(connection)

    statuses = summarize_document_embedding_status(connection)

    connection.close()

    return statuses


def load_chunks(document_id: int) -> list[dict]:
    connection = create_connection(SQLITE_DATABASE_PATH)

    create_documents_table(connection)
    create_chunks_table(connection)

    chunks = list_chunks_by_document_id(connection, document_id)

    connection.close()

    return chunks


st.set_page_config(
    page_title="文档管理",
    page_icon="📄",
    layout="wide",
)

st.title("文档管理")
st.write("查看企业知识库中的文档和切分片段。")

documents = load_documents()
embedding_statuses = load_embedding_statuses()

st.subheader("文档列表")
st.subheader("Embedding 索引状态")

if embedding_statuses == []:
    st.info("暂无 embedding 索引状态。")
else:
    st.dataframe(embedding_statuses, use_container_width=True)

st.subheader("补齐 Embedding 索引")

st.write("如果某些文档的 embedding 未完成，可以点击下面按钮补齐缺失索引。")

if st.button("补齐缺失 embeddings"):
    with st.spinner("正在调用 bge-m3 生成缺失 embeddings..."):
        result = backfill_chunk_embeddings()

    st.success("补索引完成")
    st.write("总 chunks 数量：", result["total_chunks"])
    st.write("新增 embedding 数量：", result["created"])
    st.write("已存在跳过数量：", result["skipped"])

if documents == []:
    st.info("暂无文档。")
else:
    st.dataframe(documents, use_container_width=True)

st.subheader("查看文档 chunks")

document_id = st.number_input(
    "请输入文档 ID",
    min_value=1,
    step=1,
)

if st.button("查看 chunks"):
    chunks = load_chunks(int(document_id))

    if chunks == []:
        st.warning("没有找到该文档的 chunks。")
    else:
        st.write(f"共 {len(chunks)} 个 chunks")

        for chunk in chunks:
            with st.expander(f"Chunk #{chunk['id']}"):
                st.write(chunk["text"])