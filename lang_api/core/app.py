"""FastAPI application instance and startup/shutdown logic."""

import warnings
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from transformers import logging as transformers_logging

from lang_api.api.middleware import RequestLoggingMiddleware
from lang_api.api.routes import router
from lang_api.core.config import Settings
from lang_api.core.logging import configure_logging
from lang_api.models.services import TranslationService

logger = structlog.stdlib.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Loads model on startup, cleans on shutdown.

    Args:
        app (FastAPI): FastAPI app instance.

    Yields:
        None: Application runs between startup and shutdown
    """
    warnings.filterwarnings("ignore", category=FutureWarning, module="transformers")
    transformers_logging.set_verbosity_error()

    settings = Settings()
    app.state.translation_service = TranslationService.load_models(settings)
    yield


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        settings (Settings | None, optional): Optional settings override for testing

    Returns:
        FastAPI: Configured app instance.
    """
    if settings is None:
        settings = Settings()

    configure_logging(debug=settings.debug)

    app = FastAPI(
        title="LangAPI",
        description="Translation API service serving Helsinki NLP models",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(RequestLoggingMiddleware)
    app.include_router(router)

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exception: ValueError) -> JSONResponse:
        """Handles ValueError gracefully as 400 bad request.

        Args:
            request (Request): The incoming request.
            exception (ValueError): The ValueError that was raised.

        Returns:
            JSONResponse: Error response with 400 status.
        """
        logger.warning("Bad request on %s %s: %s", request.method, request.url, exception)
        return JSONResponse(
            status_code=400,
            content={"error": "bad_request", "detail": str(exception)},
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exception: Exception) -> JSONResponse:
        """Handle unexpected errors as 500 Internal Server Error.

        Args:
            request: The incoming request.
            exception: The unhandled exception.

        Returns:
            JSONResponse: Error response with 500 status.
        """
        logger.exception("Unhandled error on %s %s", request.method, request.url)
        return JSONResponse(
            status_code=500,
            content={"error": "internal_error", "detail": "An unexpected error occurred"},
        )

    return app
