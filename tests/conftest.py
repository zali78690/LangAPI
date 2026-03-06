"""Shared fixtures for API tests."""

from collections.abc import Generator
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from lang_api.api.dependencies import get_translation_service
from lang_api.core.app import create_app
from lang_api.models.services import TranslationService


@pytest.fixture
def mock_translation_service() -> TranslationService:
    """TranslationService with mocked models for fr."""
    mock_tokenizer = MagicMock()
    mock_tokenizer.return_value = {"input_ids": MagicMock()}
    mock_tokenizer.decode.return_value = "Bonjour le monde"

    mock_model = MagicMock()
    mock_model.generate.return_value = [MagicMock()]

    return TranslationService(
        models={"fr": (mock_tokenizer, mock_model)},
        language_model_mapping={"fr": "Helsinki-NLP/opus-mt-en-fr"},
    )


@pytest.fixture
def test_client(mock_translation_service: TranslationService) -> Generator[TestClient]:
    """FastAPI TestClient with mocked translation service."""
    app = create_app()
    app.dependency_overrides[get_translation_service] = lambda: mock_translation_service
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def skip_model_loading(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prevent real model downloads during tests."""
    monkeypatch.setattr(
        "lang_api.core.app.TranslationService.load_models",
        lambda _: TranslationService(models={}, language_model_mapping={}),
    )
