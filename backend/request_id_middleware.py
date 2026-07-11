import logging
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response

from backend.config import SLOW_REQUEST_THRESHOLD_MS
from backend.request_context import reset_request_id, set_request_id


REQUEST_ID_HEADER = "X-Request-ID"

logger = logging.getLogger(__name__)


def get_current_time() -> float:
    return time.perf_counter()


def log_slow_request_if_needed(
    request: Request,
    request_id: str,
    duration_ms: float,
) -> None:
    if duration_ms < SLOW_REQUEST_THRESHOLD_MS:
        return

    logger.warning(
        "slow_request method=%s path=%s request_id=%s duration_ms=%.2f threshold_ms=%.2f",
        request.method,
        request.url.path,
        request_id,
        duration_ms,
        SLOW_REQUEST_THRESHOLD_MS,
    )


async def add_request_id(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    request_id = request.headers.get(REQUEST_ID_HEADER, str(uuid.uuid4()))
    token = set_request_id(request_id)
    start_time = get_current_time()

    logger.info(
        "request_started method=%s path=%s request_id=%s",
        request.method,
        request.url.path,
        request_id,
    )

    try:
        response = await call_next(request)
    except Exception:
        duration_ms = (get_current_time() - start_time) * 1000
        log_slow_request_if_needed(request, request_id, duration_ms)

        logger.exception(
            "request_failed method=%s path=%s request_id=%s duration_ms=%.2f",
            request.method,
            request.url.path,
            request_id,
            duration_ms,
        )
        reset_request_id(token)
        raise

    duration_ms = (get_current_time() - start_time) * 1000
    response.headers[REQUEST_ID_HEADER] = request_id
    log_slow_request_if_needed(request, request_id, duration_ms)

    logger.info(
        "request_finished method=%s path=%s status_code=%s request_id=%s duration_ms=%.2f",
        request.method,
        request.url.path,
        response.status_code,
        request_id,
        duration_ms,
    )

    reset_request_id(token)

    return response
