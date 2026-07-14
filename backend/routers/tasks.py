from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.services.task_queue_service import InMemoryTaskQueue, TaskRunner


router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])

task_queue = InMemoryTaskQueue()


class TaskCreateRequest(BaseModel):
    type: str = Field(min_length=1)
    payload: dict = Field(default_factory=dict)


def get_task_queue() -> InMemoryTaskQueue:
    return task_queue


@router.post("", status_code=201)
def create_task(
    request: TaskCreateRequest,
    queue: InMemoryTaskQueue = Depends(get_task_queue),
):
    return queue.create_task(
        task_type=request.type,
        payload=request.payload,
    )


@router.get("/{task_id}")
def get_task(
    task_id: int,
    queue: InMemoryTaskQueue = Depends(get_task_queue),
):
    task = queue.get_task(task_id)

    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在。")

    return task


def echo_task_handler(payload: dict) -> dict:
    return payload


@router.post("/{task_id}/run")
def run_task(
    task_id: int,
    queue: InMemoryTaskQueue = Depends(get_task_queue),
):
    task = queue.get_task(task_id)

    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在。")

    runner = TaskRunner(queue=queue)
    return runner.run_task(task_id, echo_task_handler)