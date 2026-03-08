"""Tests for Prometheus metrics setup."""

from fastapi.testclient import TestClient

from lang_api.core.metrics import (
    MODEL_LOAD_DURATION,
    TRANSLATION_DURATION,
    TRANSLATION_REQUESTS,
)


class TestMetricsEndpoint:
    """Tests for /metrics endpoint."""

    def test_metrics_endpoint_returns_200(self, test_client: TestClient) -> None:
        """GET /metrics returns Prometheus text format."""
        response = test_client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]

    def test_metrics_endpoint_contains_http_metrics(self, test_client: TestClient) -> None:
        """Auto HTTP metrics are present after a request."""
        test_client.get("/api/v1/languages")
        response = test_client.get("/metrics")
        assert "http_request_duration_seconds" in response.text

    def test_metrics_endpoint_not_in_openapi(self, test_client: TestClient) -> None:
        """/metrics is excluded from OpenAPI schema."""
        response = test_client.get("/openapi.json")
        assert "/metrics" not in response.text


class TestCustomMetrics:
    """Tests for custom business metrics are exposed on /metrics endpoint."""

    def test_translation_requests_counter_exposed(self, test_client: TestClient) -> None:
        """Translation counter appears in /metrics output."""
        response = test_client.get("/metrics")
        assert "translation_requests_total" in response.text

    def test_translation_duration_histogram_exposed(self, test_client: TestClient) -> None:
        """Translation duration histogram appears in /metrics output."""
        response = test_client.get("/metrics")
        assert "translation_duration_seconds" in response.text

    def test_model_load_duration_histogram_exposed(self, test_client: TestClient) -> None:
        """Model load duration histogram appears in /metrics output."""
        response = test_client.get("/metrics")
        assert "model_load_duration_seconds" in response.text

    def test_custom_metrics_have_correct_types(self) -> None:
        """Custom metrics are the expected Prometheus types."""
        assert type(TRANSLATION_REQUESTS).__name__ == "Counter"
        assert type(TRANSLATION_DURATION).__name__ == "Histogram"
        assert type(MODEL_LOAD_DURATION).__name__ == "Histogram"
