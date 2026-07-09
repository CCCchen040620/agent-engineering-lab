from backend.services.sqlite_document_repository import create_connection
from backend.services.sqlite_conversation_repository import (
    add_message,
    create_conversation,
    create_conversations_table,
    create_messages_table,
    find_conversation_by_id,
    list_conversations,
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


def test_list_conversations():
    connection = create_connection(":memory:")

    create_conversations_table(connection)

    create_conversation(connection, "第一次对话")
    create_conversation(connection, "第二次对话")

    conversations = list_conversations(connection)

    assert conversations == [
        {
            "id": 1,
            "title": "第一次对话",
        },
        {
            "id": 2,
            "title": "第二次对话",
        },
    ]

    connection.close()


def test_find_conversation_by_id():
    connection = create_connection(":memory:")

    create_conversations_table(connection)

    create_conversation(connection, "第一次对话")

    conversation = find_conversation_by_id(connection, 1)

    assert conversation == {
        "id": 1,
        "title": "第一次对话",
    }

    connection.close()


def test_find_conversation_by_id_returns_none_when_not_found():
    connection = create_connection(":memory:")

    create_conversations_table(connection)

    conversation = find_conversation_by_id(connection, 999)

    assert conversation is None

    connection.close()


def test_add_message_with_metadata():
    connection = create_connection(":memory:")

    create_conversations_table(connection)
    create_messages_table(connection)

    conversation = create_conversation(connection, "带元数据的对话")

    metadata = {
        "intent": "read_document",
        "keyword": "员工手册",
        "citations": [
            {
                "title": "员工手册",
                "text": "新员工入职后需要在 30 天内完成安全培训。",
                "path": "sqlite://1",
            }
        ],
    }

    message = add_message(
        connection,
        conversation_id=conversation["id"],
        role="assistant",
        content="员工手册 的片段如下：...",
        metadata=metadata,
    )

    assert message["id"] == 1
    assert message["conversation_id"] == conversation["id"]
    assert message["role"] == "assistant"
    assert message["content"] == "员工手册 的片段如下：..."
    assert message["metadata"] == metadata

    connection.close()


def test_list_messages_returns_metadata():
    connection = create_connection(":memory:")

    create_conversations_table(connection)
    create_messages_table(connection)

    conversation = create_conversation(connection, "读取元数据的对话")

    metadata = {
        "intent": "answer_question",
        "keyword": "安全培训",
    }

    add_message(
        connection,
        conversation_id=conversation["id"],
        role="assistant",
        content="新员工需要完成安全培训。",
        metadata=metadata,
    )

    messages = list_messages_by_conversation(
        connection,
        conversation_id=conversation["id"],
    )

    assert len(messages) == 1
    assert messages[0]["content"] == "新员工需要完成安全培训。"
    assert messages[0]["metadata"] == metadata

    connection.close()