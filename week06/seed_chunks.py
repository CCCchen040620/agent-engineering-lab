from backend.services.sqlite_document_repository import (
    create_chunks_table,
    create_connection,
    create_documents_table,
    insert_chunk_to_db,
    list_chunks_by_document_id,
)
from week04.settings import SQLITE_DATABASE_PATH


def seed_employee_handbook_chunks(connection):
    existing_chunks = list_chunks_by_document_id(connection, 1)

    if len(existing_chunks) > 0:
        return

    insert_chunk_to_db(
        connection,
        document_id=1,
        text="员工每天需要完成 8 小时工作。",
    )
    insert_chunk_to_db(
        connection,
        document_id=1,
        text="新员工入职后需要在 30 天内完成安全培训。",
    )
    insert_chunk_to_db(
        connection,
        document_id=1,
        text="公司鼓励员工持续学习，并提供内部知识库作为学习资料。",
    )


def seed_leave_policy_chunks(connection):
    existing_chunks = list_chunks_by_document_id(connection, 3)

    if len(existing_chunks) > 0:
        return

    insert_chunk_to_db(
        connection,
        document_id=3,
        text="员工请假需要提前在系统中提交申请。",
    )
    insert_chunk_to_db(
        connection,
        document_id=3,
        text="病假需要提供医院证明。",
    )
    insert_chunk_to_db(
        connection,
        document_id=3,
        text="年假需要提前 3 个工作日申请。",
    )


def main():
    connection = create_connection(SQLITE_DATABASE_PATH)

    create_documents_table(connection)
    create_chunks_table(connection)

    seed_employee_handbook_chunks(connection)
    seed_leave_policy_chunks(connection)

    connection.close()

    print("chunks 初始化完成。")


if __name__ == "__main__":
    main()