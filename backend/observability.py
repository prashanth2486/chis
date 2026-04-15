import json
import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


logger = logging.getLogger("pattern_prediction")
if not logger.handlers:
    handler = logging.StreamHandler()
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


def _error_payload(request: Request, status_code: int, message: str, details=None) -> dict:
    request_id = getattr(request.state, "request_id", "")
    return {
        "error": {
            "request_id": request_id,
            "status_code": status_code,
            "message": message,
            "details": details,
        }
    }


def setup_observability(app: FastAPI) -> None:
    @app.middleware("http")
    async def request_logging_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        started = time.time()
        response = await call_next(request)
        duration_ms = round((time.time() - started) * 1000, 2)

        response.headers["X-Request-ID"] = request_id
        log_payload = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        }
        logger.info(json.dumps(log_payload, default=str))
        return response

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        payload = _error_payload(request, exc.status_code, str(exc.detail), exc.detail)
        return JSONResponse(status_code=exc.status_code, content=payload)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        payload = _error_payload(request, 422, "Validation error", exc.errors())
        return JSONResponse(status_code=422, content=payload)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        payload = _error_payload(request, 500, "Internal server error", str(exc))
        return JSONResponse(status_code=500, content=payload)
