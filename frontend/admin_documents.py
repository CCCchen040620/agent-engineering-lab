import streamlit as st

from backend.services.sqlite_document_repository import (
    create_chunks_table,
    create_connection,
    create_documents_table,
    list_chunks_by_document_id,
    list_documents_from_db,
)
from week04.settings import SQLITE_DATABASE_PATH


def load_documents() -> list[dict]:
    connection = create_connection(SQLITE_DATABASE_PATH)

    create_documents_table(connection)

    documents = list_documents_from_db(connection)

    connection.close()

    return documents


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

st.subheader("文档列表")

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