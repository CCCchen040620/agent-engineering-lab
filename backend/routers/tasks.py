from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from backend.services.task_queue_service import InMemoryTaskQueue, TaskRunner
from backend.services.task_dispatcher_service import TaskDispatcher


router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])

task_queue = InMemoryTaskQueue()


class TaskCreateRequest(BaseModel):
    type: str = Field(min_length=1)
    payload: dict = Field(default_factory=dict)


def get_task_queue() -> InMemoryTaskQueue:
    return task_queue


def echo_task_handler(payload: dict) -> dict:
    return payload


def build_task_dispatcher() -> TaskDispatcher:
    dispatcher = TaskDispatcher()
    dispatcher.register("echo", echo_task_handler)
    return dispatcher


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


@router.post("/{task_id}/run")
def run_task(
    task_id: int,
    queue: InMemoryTaskQueue = Depends(get_task_queue),
):
    task = queue.get_task(task_id)

    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在。")

    dispatcher = build_task_dispatcher()

    def dispatch_payload(payload: dict) -> dict:
        return dispatcher.dispatch(task["type"], payload)

    runner = TaskRunner(queue=queue)
    return runner.run_task(task_id, dispatch_payload)