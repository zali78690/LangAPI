"""Unit tests for routes.py."""

from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from lang_api.api.dependencies import get_translation_service
from lang_api.core.app import create_app
from lang_api.models.services import TranslationService


class TestTranslateEndpoint:
    """Tests for POST /api/v1/translate."""

    def test_translate_success(self, test_client: TestClient):
        """200 with valid translation request."""
        response = test_client.post(
            "/api/v1/translate",
            json={"text": "Hello world", "target_language": "fr"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["translated_text"] == "Bonjour le monde"
        assert data["source_language"] == "en"
        assert data["target_language"] == "fr"

    def test_translate_missing_text_returns_422(self, test_client: TestClient):
        """422 when text field is missing."""
        response = test_client.post(
            "/api/v1/translate",
            json={"target_language": "fr"},
        )
        assert response.status_code == 422

    def test_translate_empty_text_returns_422(self, test_client: TestClient):
        """422 when text is empty string."""
        response = test_client.post(
            "/api/v1/translate",
            json={"text": "", "target_language": "fr"},
        )
        assert response.status_code == 422

    def test_translate_unsupported_language_returns_400(self, test_client: TestClient):
        """400 when target language is not supported."""
        response = test_client.post(
            "/api/v1/translate",
            json={"text": "Hello", "target_language": "ja"},
        )
        assert response.status_code == 400
        assert response.json()["error"] == "bad_request"

    def test_translate_unexpected_error_returns_500(self):
        """500 on unexpected error, no stack trace leaked."""
        mock_service = MagicMock(spec=TranslationService)
        mock_service.translate.side_effect = RuntimeError("something broke")

        app = create_app()
        app.dependency_overrides[get_translation_service] = lambda: mock_service
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.post(
                "/api/v1/translate",
                json={"text": "Hello", "target_language": "fr"},
            )
        assert response.status_code == 500
        data = response.json()
        assert data["error"] == "internal_error"
        assert "something broke" not in data["detail"]


class TestLanguagesEndpoint:
    """Tests for GET /api/v1/languages."""

    def test_get_languages_returns_mapping(self, test_client: TestClient):
        """200 returns language-to-model mapping."""
        response = test_client.get("/api/v1/languages")
        assert response.status_code == 200
        assert response.json()["supported_languages"] == {"fr": "Helsinki-NLP/opus-mt-en-fr"}


class TestHealthEndpoint:
    """Tests for GET /health."""

    def test_health_when_models_loaded(self, test_client: TestClient):
        """200 healthy when models are loaded."""
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["models_loaded"] is True
        assert "fr" in data["supported_languages"]

    def test_health_when_no_models(self, empty_translation_service: TranslationService):
        """200 unhealthy when no models loaded."""
        app = create_app()
        app.dependency_overrides[get_translation_service] = lambda: empty_translation_service
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["models_loaded"] is False
