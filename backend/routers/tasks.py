from threading import Thread

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from backend.services.task_queue_service import InMemoryTaskQueue, TaskRunner
from backend.services.task_dispatcher_service import build_default_task_dispatcher


router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])

task_queue = InMemoryTaskQueue()


class TaskCreateRequest(BaseModel):
    type: str = Field(min_length=1)
    payload: dict = Field(default_factory=dict)


def get_task_queue() -> InMemoryTaskQueue:
    return task_queue


def build_task_handler(task: dict):
    dispatcher = build_default_task_dispatcher()

    return lambda payload: dispatcher.dispatch(task["type"], payload)


def get_task_or_404(task_id: int, queue: InMemoryTaskQueue) -> dict:
    task = queue.get_task(task_id)

    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在。")

    return task


def run_task_by_id(task_id: int, queue: InMemoryTaskQueue) -> dict:
    task = get_task_or_404(task_id, queue)
    runner = TaskRunner(queue=queue)

    return runner.run_task(task_id, build_task_handler(task))


def finish_running_task_by_id(task_id: int, queue: InMemoryTaskQueue) -> dict:
    task = queue.get_task(task_id)

    if task is None:
        return {}

    runner = TaskRunner(queue=queue)
    return runner.finish_running_task(task_id, build_task_handler(task))


def start_task_thread(task_id: int, queue: InMemoryTaskQueue) -> None:
    thread = Thread(
        target=finish_running_task_by_id,
        args=(task_id, queue),
        daemon=True,
    )
    thread.start()


@router.post("", status_code=201)
def create_task(
    request: TaskCreateRequest,
    queue: InMemoryTaskQueue = Depends(get_task_queue),
):
    return queue.create_task(
        task_type=request.type,
        payload=request.payload,
    )


@router.get("")
def list_tasks(
    queue: InMemoryTaskQueue = Depends(get_task_queue),
):
    return queue.list_tasks()

    
@router.get("/{task_id}")
def get_task(
    task_id: int,
    queue: InMemoryTaskQueue = Depends(get_task_queue),
):
    task = queue.get_task(task_id)

    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在。")

    return task


@router.post("/{task_id}/run")
def run_task(
    task_id: int,
    queue: InMemoryTaskQueue = Depends(get_task_queue),
):
    return run_task_by_id(task_id, queue)


@router.post("/{task_id}/run-async", status_code=202)
def run_task_async(
    task_id: int,
    queue: InMemoryTaskQueue = Depends(get_task_queue),
):
    task = get_task_or_404(task_id, queue)
    queue.mark_task_running(task_id)
    start_task_thread(task_id, queue)

    return task


@router.post("/postgresql-embedding-backfill")
def create_and_run_postgresql_embedding_backfill_task(
    queue: InMemoryTaskQueue = Depends(get_task_queue),
):
    task = queue.create_task(
        task_type="postgresql_embedding_backfill",
        payload={},
    )

    return run_task_by_id(task["id"], queue)
