"""Prometheus metrics for LangAPI (ADR-008)."""

from fastapi import FastAPI
from prometheus_client import Counter, Histogram
from prometheus_fastapi_instrumentator import Instrumentator

TRANSLATION_REQUESTS = Counter(
    "translation_requests_total",
    "Total translation requests by target language.",
    labelnames=("target_language",),
)

TRANSLATION_DURATION = Histogram(
    "translation_duration_seconds",
    "Time spent on model inference by target language.",
    labelnames=("target_language",),
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

MODEL_LOAD_DURATION = Histogram(
    "model_load_duration_seconds",
    "Time to load a translation model.",
    labelnames=("language",),
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0),
)


def setup_metrics(app: FastAPI) -> None:
    """Configure Prometheus metrics and expose /metrics endpoint.

    Args:
        app: FastAPI application instance.
    """
    Instrumentator(
        excluded_handlers=["/health", "/metrics"],
        should_ignore_untemplated=True,
    ).instrument(app).expose(app, include_in_schema=False)
