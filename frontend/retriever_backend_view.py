SQLITE_BACKEND = "sqlite"
POSTGRESQL_BACKEND = "postgresql"


def get_default_retriever_backend_from_info(info: dict | None) -> str:
    if info is None:
        return SQLITE_BACKEND

    backend = info.get("default_rag_retriever_backend", SQLITE_BACKEND)

    if backend == POSTGRESQL_BACKEND:
        return POSTGRESQL_BACKEND

    return SQLITE_BACKEND


def get_retriever_backend_radio_index(info: dict | None) -> int:
    if get_default_retriever_backend_from_info(info) == POSTGRESQL_BACKEND:
        return 1

    return 0


def get_chat_engine_radio_index(info: dict | None) -> int:
    if get_default_retriever_backend_from_info(info) == POSTGRESQL_BACKEND:
        return 2

    return 0


def get_retriever_backend_override(
    info: dict | None,
    selected_backend: str,
) -> str | None:
    default_backend = get_default_retriever_backend_from_info(info)

    if selected_backend == default_backend:
        return None

    return selected_backend


def build_retriever_backend_caption(
    info: dict | None,
    selected_backend: str,
) -> str:
    database_backend = "unknown"
    default_backend = get_default_retriever_backend_from_info(info)

    if info is not None:
        database_backend = info.get("database_backend", "unknown")

    return (
        f"主数据库：{database_backend} | "
        f"默认检索后端：{default_backend} | "
        f"当前选择：{selected_backend}"
    )
