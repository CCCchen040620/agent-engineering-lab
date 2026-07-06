from backend.services.sqlite_document_repository import create_connection
from backend.services.sqlite_feedback_repository import (
    create_feedback_table,
    insert_feedback_to_db,
    list_feedback_from_db,
)


def test_insert_feedback_to_db(tmp_path):
    database_path = tmp_path / "test.db"
    connection = create_connection(str(database_path))

    create_feedback_table(connection)

    feedback = insert_feedback_to_db(
        connection,
        question="新员工什么时候完成安全培训？",
        answer="新员工需要在 30 天内完成安全培训。",
        rating="helpful",
    )

    connection.close()

    assert feedback["id"] == 1
    assert feedback["question"] == "新员工什么时候完成安全培训？"
    assert feedback["rating"] == "helpful"


def test_list_feedback_from_db(tmp_path):
    database_path = tmp_path / "test.db"
    connection = create_connection(str(database_path))

    create_feedback_table(connection)

    insert_feedback_to_db(
        connection,
        question="公司有没有股票期权？",
        answer="知识库中没有找到相关资料，暂时无法回答。",
        rating="not_helpful",
    )

    feedback_items = list_feedback_from_db(connection)

    connection.close()

    assert len(feedback_items) == 1
    assert feedback_items[0]["rating"] == "not_helpful"