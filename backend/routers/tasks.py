from threading import Thread

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from backend.config import DATABASE_URL
from backend.services.database_url_service import is_postgresql_database
from backend.services.postgresql_task_repository import PostgresqlTaskQueue
from backend.services.task_queue_service import InMemoryTaskQueue, TaskRunner
from backend.services.task_dispatcher_service import build_default_task_dispatcher


router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


class TaskCreateRequest(BaseModel):
    type: str = Field(min_length=1)
    payload: dict = Field(default_factory=dict)


class PostgreSQLDocumentIngestionTaskRequest(BaseModel):
    title: str = Field(min_length=1)
    file_type: str = Field(min_length=1)
    content: str = Field(min_length=1)
    source: str = "production"


def build_default_task_queue(database_url: str = DATABASE_URL):
    if is_postgresql_database(database_url):
        return PostgresqlTaskQueue(
            connection_factory=lambda: psycopg.connect(database_url),
        )

    return InMemoryTaskQueue()


task_queue = build_default_task_queue()


def get_task_queue():
    return task_queue


def build_task_handler(task: dict):
    dispatcher = build_default_task_dispatcher()

    return lambda payload: dispatcher.dispatch(task["type"], payload)


def get_task_or_404(task_id: int, queue) -> dict:
    task = queue.get_task(task_id)

    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在。")

    return task


def run_task_by_id(task_id: int, queue) -> dict:
    task = get_task_or_404(task_id, queue)
    runner = TaskRunner(queue=queue)

    return runner.run_task(task_id, build_task_handler(task))


def create_retry_task_from_failed_task(task_id: int, queue) -> dict:
    task = get_task_or_404(task_id, queue)

    if task["status"] != "failed":
        raise HTTPException(status_code=409, detail="只有失败任务可以重试。")

    return queue.create_task(
        task_type=task["type"],
        payload=task["payload"],
        retry_of_task_id=task["id"],
    )


def cancel_pending_task(task_id: int, queue) -> dict:
    task = get_task_or_404(task_id, queue)

    if task["status"] != "pending":
        raise HTTPException(status_code=409, detail="只有等待执行的任务可以取消。")

    return queue.mark_task_canceled(task_id)


def finish_running_task_by_id(task_id: int, queue) -> dict:
    task = queue.get_task(task_id)

    if task is None:
        return {}

    runner = TaskRunner(queue=queue)
    return runner.finish_running_task(task_id, build_task_handler(task))


def start_task_thread(task_id: int, queue) -> None:
    thread = Thread(
        target=finish_running_task_by_id,
        args=(task_id, queue),
        daemon=True,
    )
    thread.start()


def build_postgresql_document_ingestion_payload(
    request: PostgreSQLDocumentIngestionTaskRequest,
) -> dict:
    return {
        "title": request.title,
        "file_type": request.file_type,
        "content": request.content,
        "source": request.source,
    }


@router.post("", status_code=201)
def create_task(
    request: TaskCreateRequest,
    queue=Depends(get_task_queue),
):
    return queue.create_task(
        task_type=request.type,
        payload=request.payload,
    )


@router.get("")
def list_tasks(
    status: str | None = Query(default=None),
    order: str = Query(default="desc"),
    limit: int | None = Query(default=None, ge=1),
    queue=Depends(get_task_queue),
):
    return queue.list_tasks(status=status, order=order, limit=limit)

    
@router.get("/{task_id}")
def get_task(
    task_id: int,
    queue=Depends(get_task_queue),
):
    task = queue.get_task(task_id)

    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在。")

    return task


@router.post("/{task_id}/run")
def run_task(
    task_id: int,
    queue=Depends(get_task_queue),
):
    return run_task_by_id(task_id, queue)


@router.post("/postgresql-document-ingestion/run-async", status_code=202)
def create_and_run_postgresql_document_ingestion_task_async(
    request: PostgreSQLDocumentIngestionTaskRequest,
    queue=Depends(get_task_queue),
):
    task = queue.create_task(
        task_type="postgresql_document_ingestion",
        payload=build_postgresql_document_ingestion_payload(request),
    )
    running_task = queue.mark_task_running(task["id"])
    start_task_thread(task["id"], queue)

    return running_task


@router.post("/{task_id}/run-async", status_code=202)
def run_task_async(
    task_id: int,
    queue=Depends(get_task_queue),
):
    get_task_or_404(task_id, queue)
    running_task = queue.mark_task_running(task_id)
    start_task_thread(task_id, queue)

    return running_task


@router.post("/{task_id}/retry-async", status_code=202)
def retry_task_async(
    task_id: int,
    queue=Depends(get_task_queue),
):
    retry_task = create_retry_task_from_failed_task(task_id, queue)
    running_task = queue.mark_task_running(retry_task["id"])
    start_task_thread(retry_task["id"], queue)

    return running_task


@router.post("/{task_id}/cancel")
def cancel_task(
    task_id: int,
    queue=Depends(get_task_queue),
):
    return cancel_pending_task(task_id, queue)


@router.post("/postgresql-embedding-backfill")
def create_and_run_postgresql_embedding_backfill_task(
    queue=Depends(get_task_queue),
):
    task = queue.create_task(
        task_type="postgresql_embedding_backfill",
        payload={},
    )

    return run_task_by_id(task["id"], queue)


@router.post("/postgresql-document-ingestion")
def create_and_run_postgresql_document_ingestion_task(
    request: PostgreSQLDocumentIngestionTaskRequest,
    queue=Depends(get_task_queue),
):
    task = queue.create_task(
        task_type="postgresql_document_ingestion",
        payload=build_postgresql_document_ingestion_payload(request),
    )

    return run_task_by_id(task["id"], queue)
