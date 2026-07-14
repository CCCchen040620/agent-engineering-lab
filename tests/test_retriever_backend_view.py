from frontend.retriever_backend_view import (
    build_retriever_backend_caption,
    get_chat_engine_radio_index,
    get_default_retriever_backend_from_info,
    get_retriever_backend_override,
    get_retriever_backend_radio_index,
)


def test_get_default_retriever_backend_from_info_defaults_to_sqlite():
    assert get_default_retriever_backend_from_info(None) == "sqlite"
    assert get_retriever_backend_radio_index(None) == 0
    assert get_chat_engine_radio_index(None) == 0


def test_get_default_retriever_backend_from_info_uses_postgresql():
    info = {
        "database_backend": "postgresql",
        "default_rag_retriever_backend": "postgresql",
    }

    assert get_default_retriever_backend_from_info(info) == "postgresql"
    assert get_retriever_backend_radio_index(info) == 1
    assert get_chat_engine_radio_index(info) == 2


def test_build_retriever_backend_caption():
    caption = build_retriever_backend_caption(
        {
            "database_backend": "postgresql",
            "default_rag_retriever_backend": "postgresql",
        },
        selected_backend="sqlite",
    )

    assert caption == "主数据库：postgresql | 默认检索后端：postgresql | 当前选择：sqlite"


def test_get_retriever_backend_override_returns_none_for_default_backend():
    info = {
        "database_backend": "postgresql",
        "default_rag_retriever_backend": "postgresql",
    }

    assert get_retriever_backend_override(info, "postgresql") is None


def test_get_retriever_backend_override_returns_selected_backend_when_overridden():
    info = {
        "database_backend": "postgresql",
        "default_rag_retriever_backend": "postgresql",
    }

    assert get_retriever_backend_override(info, "sqlite") == "sqlite"
