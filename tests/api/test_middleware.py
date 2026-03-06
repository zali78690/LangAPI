"""Tests for request logging middleware."""

import logging

import pytest
from fastapi.testclient import TestClient


class TestRequestLoggingMiddleware:
    """Tests for RequestLoggingMiddleware."""

    def test_response_has_request_id_header(self, test_client: TestClient) -> None:
        """Every response gets an X-Request-ID header."""
        response = test_client.get("/api/v1/languages")
        assert "x-request-id" in response.headers
        assert len(response.headers["x-request-id"]) > 0

    def test_preserves_client_request_id(self, test_client: TestClient) -> None:
        """Client-provided X-Request-ID is echoed back."""
        response = test_client.get(
            "/api/v1/languages",
            headers={"X-Request-ID": "my-trace-123"},
        )
        assert response.headers["x-request-id"] == "my-trace-123"

    def test_health_endpoint_not_logged(self, test_client: TestClient, caplog: pytest.LogCaptureFixture) -> None:
        """Health endpoint requests are excluded from request logging."""
        with caplog.at_level(logging.INFO):
            test_client.get("/health")
        request_logs = [r for r in caplog.records if r.getMessage() in ("request_started", "request_completed")]
        assert len(request_logs) == 0

    def test_metrics_endpoint_not_logged(self, test_client: TestClient, caplog: pytest.LogCaptureFixture) -> None:
        """/metrics requests are excluded from request logging."""
        with caplog.at_level(logging.INFO):
            test_client.get("/metrics")
        request_logs = [r for r in caplog.records if r.getMessage() in ("request_started", "request_completed")]
        assert len(request_logs) == 0

    def test_regular_endpoint_is_logged(self, test_client: TestClient, caplog: pytest.LogCaptureFixture) -> None:
        """Non-health endpoints produce request_started and request_completed logs."""
        with caplog.at_level(logging.INFO):
            test_client.get("/api/v1/languages")
        log_text = " ".join(r.getMessage() for r in caplog.records)
        assert "request_started" in log_text
        assert "request_completed" in log_text
