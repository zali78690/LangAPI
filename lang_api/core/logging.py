"""Logging configuration for LangAPI (ADR-004, ADR-007)."""

import logging
import sys

import structlog


def configure_logging(debug: bool = False) -> None:
    """Configure structlog with JSON (production) or console (development) output.

    Args:
        debug: If True, use human-readable console renderer. If False, use JSON.
    """
    renderer: structlog.types.Processor = (
        structlog.dev.ConsoleRenderer() if debug else structlog.processors.JSONRenderer()
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            renderer,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Route stdlib logging (e.g. uvicorn) through structlog processors
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=logging.INFO, force=True)

    # Silence noisy HTTP logs from HuggingFace model downloads
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("huggingface_hub").setLevel(logging.WARNING)
