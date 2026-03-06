"""Request logging and correlation ID middleware."""

import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.stdlib.get_logger(__name__)

SKIP_PATHS = frozenset({"/health"})


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs every request with timing and correlation ID.

    Uses structlog contextvars so request_id, method, and path are
    automatically included in all log lines within the request scope.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Process request with logging and correlation ID.

        Args:
            request: Incoming HTTP request.
            call_next: Next middleware/handler in the chain.

        Returns:
            Response with X-Request-ID header.
        """
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        if request.url.path in SKIP_PATHS:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response

        logger.info("request_started")

        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        logger.info("request_completed", status_code=response.status_code, duration_ms=duration_ms)

        response.headers["X-Request-ID"] = request_id
        return response
