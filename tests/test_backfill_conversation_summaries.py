from backend.services.sqlite_conversation_repository import (
    add_message,
    create_conversation,
    create_conversations_table,
    create_messages_table,
    find_conversation_by_id,
)
from backend.services.sqlite_document_repository import create_connection
from week10.backfill_conversation_summaries import (
    backfill_conversation_summaries,
)


def test_backfill_conversation_summaries_updates_empty_summary(tmp_path):
    database_path = tmp_path / "test.db"
    connection = create_connection(str(database_path))

    create_conversations_table(connection)
    create_messages_table(connection)

    conversation = create_conversation(connection, "员工手册问答")

    add_message(
        connection,
        conversation_id=conversation["id"],
        role="user",
        content="每天需要工作多久？",
        metadata={
            "question": "每天需要工作多久？",
        },
    )

    add_message(
        connection,
        conversation_id=conversation["id"],
        role="assistant",
        content="员工每天需要完成 8 小时工作。",
        metadata={
            "citations": [
                {
                    "title": "员工手册",
                    "text": "员工每天需要完成 8 小时工作。",
                    "path": "sqlite://1",
                }
            ]
        },
    )

    connection.close()

    result = backfill_conversation_summaries(str(database_path))

    connection = create_connection(str(database_path))
    updated_conversation = find_conversation_by_id(
        connection,
        conversation["id"],
    )
    connection.close()

    assert result == {
        "total_conversations": 1,
        "updated": 1,
        "skipped": 0,
    }
    assert updated_conversation["summary"] == "最近问题：每天需要工作多久？；最近引用文档：员工手册。"


def test_backfill_conversation_summaries_skips_existing_summary(tmp_path):
    database_path = tmp_path / "test.db"
    connection = create_connection(str(database_path))

    create_conversations_table(connection)
    create_messages_table(connection)

    conversation = create_conversation(connection, "已有摘要会话")

    from backend.services.sqlite_conversation_repository import (
        update_conversation_summary,
    )

    update_conversation_summary(
        connection,
        conversation_id=conversation["id"],
        summary="已有摘要",
    )

    connection.close()

    result = backfill_conversation_summaries(str(database_path))

    assert result == {
        "total_conversations": 1,
        "updated": 0,
        "skipped": 1,
    }


def test_backfill_conversation_summaries_skips_when_no_summary_can_be_built(tmp_path):
    database_path = tmp_path / "test.db"
    connection = create_connection(str(database_path))

    create_conversations_table(connection)
    create_messages_table(connection)

    create_conversation(connection, "空会话")

    connection.close()

    result = backfill_conversation_summaries(str(database_path))

    assert result == {
        "total_conversations": 1,
        "updated": 0,
        "skipped": 1,
    }