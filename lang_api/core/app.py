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
from lang_api.api.schemas import ErrorResponse
from lang_api.core.config import Settings
from lang_api.core.logging import configure_logging
from lang_api.core.metrics import setup_metrics
from lang_api.models.services import TranslationService

logger = structlog.stdlib.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Manages application startup and shutdown lifecycle.

    Startup: loads translation models into memory.
    Shutdown: releases model references for clean garbage collection.

    Args:
        app (FastAPI): FastAPI app instance.

    Yields:
        None: Application runs between startup and shutdown.
    """
    warnings.filterwarnings("ignore", category=FutureWarning, module="transformers")
    transformers_logging.set_verbosity_error()

    app.state.translation_service = TranslationService.load_models(app.state.settings)
    logger.info("startup_complete", languages=app.state.translation_service.supported_languages)
    yield
    # Shutdown: release model references so garbage collector can reclaim GPU/CPU memory
    logger.info("shutdown", action="releasing_models")
    app.state.translation_service = None


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

    app.state.settings = settings
    app.add_middleware(RequestLoggingMiddleware)
    setup_metrics(app)
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
        logger.warning("bad_request", method=request.method, path=request.url.path, detail=str(exception))
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(error="bad_request", detail=str(exception)).model_dump(),
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
        logger.exception("unhandled_error", method=request.method, path=request.url.path)
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(error="internal_error", detail="An unexpected error occurred").model_dump(),
        )

    return app
