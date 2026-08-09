"""
HTTP request/response logging middleware.

Logs: method, path, status_code, duration_ms, client IP.
Never logs: request bodies, response bodies, Authorization headers, cookies.
"""

import time
import uuid

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger(__name__)

# Paths to skip (health checks, static files — would flood logs)
_SKIP_PATHS = {"/api/health", "/socket.io", "/widget"}


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip noisy or non-API paths
        path = request.url.path
        if any(path.startswith(p) for p in _SKIP_PATHS):
            return await call_next(request)

        request_id = str(uuid.uuid4())[:8]
        start = time.perf_counter()

        # Bind request-scoped fields so every log line in this request carries them
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=path,
            client_ip=request.client.host if request.client else "unknown",
        )

        logger.info("request_started")

        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.error(
                "request_failed",
                duration_ms=duration_ms,
                error=str(exc),
            )
            raise

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        level = "warning" if response.status_code >= 400 else "info"
        getattr(logger, level)(
            "request_finished",
            status_code=response.status_code,
            duration_ms=duration_ms,
        )

        # Attach request ID to response so clients can trace errors
        response.headers["X-Request-ID"] = request_id
        return response
