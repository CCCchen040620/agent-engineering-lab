import pytest

from backend.services.task_dispatcher_service import (
    UnsupportedTaskTypeError,
    TaskDispatcher,
)


def test_task_dispatcher_runs_registered_handler():
    dispatcher = TaskDispatcher()

    dispatcher.register(
        "echo",
        lambda payload: {"echo": payload["message"]},
    )

    result = dispatcher.dispatch(
        task_type="echo",
        payload={"message": "hello"},
    )

    assert result == {"echo": "hello"}


def test_task_dispatcher_raises_error_for_unsupported_task_type():
    dispatcher = TaskDispatcher()

    with pytest.raises(UnsupportedTaskTypeError):
        dispatcher.dispatch(
            task_type="unknown_task",
            payload={},
        )