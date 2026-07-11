from fastapi import APIRouter, Depends

from backend.services.sqlite_document_repository import create_connection
from backend.services.sqlite_feedback_repository import (
    create_feedback_table,
    insert_feedback_to_db,
    list_feedback_from_db,
    summarize_feedback_from_db,
)
from backend.config import DATABASE_PATH
from week05.models import Feedback, FeedbackCreateRequest


router = APIRouter(prefix="/api/v1")


def get_feedback_database_path() -> str:
    return DATABASE_PATH


@router.post("/feedback", response_model=Feedback, status_code=201)
def create_feedback(
    request: FeedbackCreateRequest,
    database_path: str = Depends(get_feedback_database_path),
):
    connection = create_connection(database_path)

    create_feedback_table(connection)

    feedback = insert_feedback_to_db(
        connection,
        question=request.question,
        answer=request.answer,
        rating=request.rating,
    )

    connection.close()

    return feedback


@router.get("/feedback", response_model=list[Feedback])
def list_feedback(
    database_path: str = Depends(get_feedback_database_path),
):
    connection = create_connection(database_path)

    create_feedback_table(connection)

    feedback_items = list_feedback_from_db(connection)

    connection.close()

    return feedback_items


@router.get("/feedback/summary")
def get_feedback_summary(
    database_path: str = Depends(get_feedback_database_path),
):
    connection = create_connection(database_path)

    create_feedback_table(connection)

    summary = summarize_feedback_from_db(connection)

    connection.close()

    return summary