from fastapi import Depends, HTTPException, Request

from backend.config import RATE_LIMIT_MAX_REQUESTS, RATE_LIMIT_WINDOW_SECONDS
from backend.services.rate_limit_service import InMemoryRateLimiter


RATE_LIMIT_ERROR_MESSAGE = "请求过于频繁，请稍后再试。"


heavy_request_rate_limiter = InMemoryRateLimiter(
    max_requests=RATE_LIMIT_MAX_REQUESTS,
    window_seconds=RATE_LIMIT_WINDOW_SECONDS,
)


def get_heavy_request_rate_limiter() -> InMemoryRateLimiter:
    return heavy_request_rate_limiter


def enforce_heavy_request_rate_limit(
    request: Request,
    limiter: InMemoryRateLimiter = Depends(get_heavy_request_rate_limiter),
) -> None:
    client_host = "unknown"

    if request.client is not None:
        client_host = request.client.host

    key = f"{client_host}:{request.url.path}"
    result = limiter.check(key)

    if not result["allowed"]:
        raise HTTPException(
            status_code=429,
            detail=RATE_LIMIT_ERROR_MESSAGE,
            headers={
                "Retry-After": str(result["retry_after_seconds"]),
            },
        )
