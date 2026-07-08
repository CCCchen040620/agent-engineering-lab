from backend.services.sqlite_document_repository import create_connection
from backend.services.sqlite_conversation_repository import (
    add_message,
    create_conversation,
    create_conversations_table,
    create_messages_table,
    list_messages_by_conversation,
)


def test_create_conversation():
    connection = create_connection(":memory:")

    create_conversations_table(connection)

    conversation = create_conversation(connection, "第一次对话")

    assert conversation["id"] == 1
    assert conversation["title"] == "第一次对话"

    connection.close()


def test_add_message():
    connection = create_connection(":memory:")

    create_conversations_table(connection)
    create_messages_table(connection)

    conversation = create_conversation(connection, "第一次对话")

    message = add_message(
        connection,
        conversation_id=conversation["id"],
        role="user",
        content="我叫陈晨",
    )

    assert message["id"] == 1
    assert message["conversation_id"] == conversation["id"]
    assert message["role"] == "user"
    assert message["content"] == "我叫陈晨"

    connection.close()


def test_list_messages_by_conversation():
    connection = create_connection(":memory:")

    create_conversations_table(connection)
    create_messages_table(connection)

    first_conversation = create_conversation(connection, "第一次对话")
    second_conversation = create_conversation(connection, "第二次对话")

    add_message(
        connection,
        conversation_id=first_conversation["id"],
        role="user",
        content="我叫陈晨",
    )

    add_message(
        connection,
        conversation_id=first_conversation["id"],
        role="assistant",
        content="我记住了，你叫陈晨。",
    )

    add_message(
        connection,
        conversation_id=second_conversation["id"],
        role="user",
        content="我叫什么？",
    )

    messages = list_messages_by_conversation(
        connection,
        conversation_id=first_conversation["id"],
    )

    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "我叫陈晨"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "我记住了，你叫陈晨。"

    connection.close()


def test_list_messages_returns_empty_list_when_conversation_has_no_messages():
    connection = create_connection(":memory:")

    create_conversations_table(connection)
    create_messages_table(connection)

    conversation = create_conversation(connection, "空对话")

    messages = list_messages_by_conversation(
        connection,
        conversation_id=conversation["id"],
    )

    assert messages == []

    connection.close()