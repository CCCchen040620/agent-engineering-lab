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


def run_task_by_id(task_id: int, queue: InMemoryTaskQueue) -> dict:
    task = queue.get_task(task_id)

    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在。")

    dispatcher = build_default_task_dispatcher()
    runner = TaskRunner(queue=queue)

    return runner.run_task(
        task_id,
        lambda payload: dispatcher.dispatch(task["type"], payload),
    )


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


@router.post("/postgresql-embedding-backfill")
def create_and_run_postgresql_embedding_backfill_task(
    queue: InMemoryTaskQueue = Depends(get_task_queue),
):
    task = queue.create_task(
        task_type="postgresql_embedding_backfill",
        payload={},
    )

    return run_task_by_id(task["id"], queue)