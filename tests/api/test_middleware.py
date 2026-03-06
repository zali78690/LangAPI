"""Tests for request logging middleware."""

import logging
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from lang_api.api.dependencies import get_translation_service
from lang_api.core.app import create_app
from lang_api.models.services import TranslationService


@pytest.fixture
def client() -> TestClient:
    """Test client with middleware active."""
    app = create_app()
    mock_service = TranslationService(
        models={"fr": (MagicMock(), MagicMock())},
        language_model_mapping={"fr": "Helsinki-NLP/opus-mt-en-fr"},
    )
    app.dependency_overrides[get_translation_service] = lambda: mock_service
    return TestClient(app, raise_server_exceptions=False)


class TestRequestLoggingMiddleware:
    """Tests for RequestLoggingMiddleware."""

    def test_response_has_request_id_header(self, client: TestClient) -> None:
        """Every response gets an X-Request-ID header."""
        response = client.get("/api/v1/languages")
        assert "x-request-id" in response.headers
        assert len(response.headers["x-request-id"]) > 0

    def test_preserves_client_request_id(self, client: TestClient) -> None:
        """Client-provided X-Request-ID is echoed back."""
        response = client.get(
            "/api/v1/languages",
            headers={"X-Request-ID": "my-trace-123"},
        )
        assert response.headers["x-request-id"] == "my-trace-123"

    def test_health_endpoint_not_logged(self, client: TestClient, caplog: pytest.LogCaptureFixture) -> None:
        """Health endpoint requests are excluded from request logging."""
        with caplog.at_level(logging.INFO):
            client.get("/health")
        request_logs = [r for r in caplog.records if r.getMessage() in ("request_started", "request_completed")]
        assert len(request_logs) == 0

    def test_regular_endpoint_is_logged(self, client: TestClient, caplog: pytest.LogCaptureFixture) -> None:
        """Non-health endpoints produce request_started and request_completed logs."""
        with caplog.at_level(logging.INFO):
            client.get("/api/v1/languages")
        log_text = " ".join(r.getMessage() for r in caplog.records)
        assert "request_started" in log_text
        assert "request_completed" in log_text
