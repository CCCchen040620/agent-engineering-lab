from fastapi import APIRouter, Depends, HTTPException, status

from backend.routers.db_documents import get_database_path
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
from week05.models import ConversationCreateRequest, MessageCreateRequest


router = APIRouter(prefix="/api/v1/conversations")


@router.post("", status_code=status.HTTP_201_CREATED)
def create_conversation_endpoint(
    request: ConversationCreateRequest,
    database_path: str = Depends(get_database_path),
):
    connection = create_connection(database_path)

    create_conversations_table(connection)

    conversation = create_conversation(
        connection,
        title=request.title,
    )

    connection.close()

    return conversation


@router.get("")
def list_conversations_endpoint(
    database_path: str = Depends(get_database_path),
):
    connection = create_connection(database_path)

    create_conversations_table(connection)

    conversations = list_conversations(connection)

    connection.close()

    return conversations


@router.get("/{conversation_id}")
def get_conversation_by_id_endpoint(
    conversation_id: int,
    database_path: str = Depends(get_database_path),
):
    connection = create_connection(database_path)

    create_conversations_table(connection)

    conversation = find_conversation_by_id(connection, conversation_id)

    connection.close()

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="会话不存在。",
        )

    return conversation

    
@router.get("/{conversation_id}/messages")
def list_conversation_messages_endpoint(
    conversation_id: int,
    database_path: str = Depends(get_database_path),
):
    connection = create_connection(database_path)

    create_conversations_table(connection)
    create_messages_table(connection)

    conversation = find_conversation_by_id(connection, conversation_id)

    if conversation is None:
        connection.close()
        raise HTTPException(
            status_code=404,
            detail="会话不存在。",
        )

    messages = list_messages_by_conversation(connection, conversation_id)

    connection.close()

    return messages


@router.post("/{conversation_id}/messages", status_code=status.HTTP_201_CREATED)
def add_conversation_message_endpoint(
    conversation_id: int,
    request: MessageCreateRequest,
    database_path: str = Depends(get_database_path),
):
    connection = create_connection(database_path)

    create_conversations_table(connection)
    create_messages_table(connection)

    conversation = find_conversation_by_id(connection, conversation_id)

    if conversation is None:
        connection.close()
        raise HTTPException(
            status_code=404,
            detail="会话不存在。",
        )

    message = add_message(
        connection,
        conversation_id=conversation_id,
        role=request.role,
        content=request.content,
    )

    connection.close()

    return message