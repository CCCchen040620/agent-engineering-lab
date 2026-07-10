from backend.services.conversation_summary_service import (
    build_conversation_summary,
)
from backend.services.sqlite_conversation_repository import (
    create_conversations_table,
    create_messages_table,
    list_conversations,
    list_messages_by_conversation,
    update_conversation_summary,
)
from backend.services.sqlite_document_repository import create_connection
from week04.settings import SQLITE_DATABASE_PATH


def backfill_conversation_summaries(
    database_path: str = SQLITE_DATABASE_PATH,
) -> dict:
    connection = create_connection(database_path)

    create_conversations_table(connection)
    create_messages_table(connection)

    conversations = list_conversations(connection)

    updated_count = 0
    skipped_count = 0

    for conversation in conversations:
        if conversation["summary"] != "":
            skipped_count = skipped_count + 1
            continue

        messages = list_messages_by_conversation(
            connection,
            conversation_id=conversation["id"],
        )

        summary = build_conversation_summary(messages)

        if summary == "":
            skipped_count = skipped_count + 1
            continue

        update_conversation_summary(
            connection,
            conversation_id=conversation["id"],
            summary=summary,
        )

        updated_count = updated_count + 1

    connection.close()

    return {
        "total_conversations": len(conversations),
        "updated": updated_count,
        "skipped": skipped_count,
    }


def main() -> None:
    result = backfill_conversation_summaries()

    print("总会话数量：", result["total_conversations"])
    print("新增摘要数量：", result["updated"])
    print("跳过数量：", result["skipped"])


if __name__ == "__main__":
    main()