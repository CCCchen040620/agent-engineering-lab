import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.request_context import get_request_id


logger = logging.getLogger(__name__)


ERROR_CODES_BY_STATUS = {
    400: "bad_request",
    404: "not_found",
    409: "conflict",
    413: "payload_too_large",
    422: "validation_error",
    429: "rate_limited",
    503: "service_unavailable",
}


def get_error_code(status_code: int) -> str:
    if status_code >= 500:
        return "internal_server_error"

    return ERROR_CODES_BY_STATUS.get(status_code, "http_error")


def build_error_response(
    *,
    status_code: int,
    detail: Any,
    message: str,
    code: str | None = None,
) -> dict:
    return {
        "detail": detail,
        "error": {
            "code": code or get_error_code(status_code),
            "message": message,
            "status_code": status_code,
        },
        "request_id": get_request_id(),
    }


def get_message_from_detail(detail: Any) -> str:
    if isinstance(detail, str):
        return detail

    return "请求处理失败。"


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    status_code = exc.status_code
    detail = exc.detail
    message = get_message_from_detail(detail)

    return JSONResponse(
        status_code=status_code,
        content=build_error_response(
            status_code=status_code,
            detail=detail,
            message=message,
        ),
        headers=getattr(exc, "headers", None),
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=build_error_response(
            status_code=422,
            detail=exc.errors(),
            message="请求参数校验失败。",
            code="validation_error",
        ),
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    logger.exception("unhandled_api_error path=%s", request.url.path)

    return JSONResponse(
        status_code=500,
        content=build_error_response(
            status_code=500,
            detail="服务器内部错误。",
            message="服务器内部错误。",
            code="internal_server_error",
        ),
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
