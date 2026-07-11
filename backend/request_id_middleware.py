import logging
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response

from backend.request_context import reset_request_id, set_request_id


REQUEST_ID_HEADER = "X-Request-ID"

logger = logging.getLogger(__name__)


async def add_request_id(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    request_id = request.headers.get(REQUEST_ID_HEADER, str(uuid.uuid4()))
    token = set_request_id(request_id)
    start_time = time.perf_counter()

    logger.info(
        "request_started method=%s path=%s request_id=%s",
        request.method,
        request.url.path,
        request_id,
    )

    try:
        response = await call_next(request)
    except Exception:
        duration_ms = (time.perf_counter() - start_time) * 1000

        logger.exception(
            "request_failed method=%s path=%s request_id=%s duration_ms=%.2f",
            request.method,
            request.url.path,
            request_id,
            duration_ms,
        )
        reset_request_id(token)
        raise

    duration_ms = (time.perf_counter() - start_time) * 1000
    response.headers[REQUEST_ID_HEADER] = request_id

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
