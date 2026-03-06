"""Unit tests for services.py."""

from unittest.mock import MagicMock

import pytest

from lang_api.models.services import TranslationService


@pytest.fixture
def mock_tokenizer() -> MagicMock:
    """Fake tokenizer that returns a dummy tensor and decodes to a string."""
    tokenizer = MagicMock()
    tokenizer.return_value = {"input_ids": MagicMock()}
    tokenizer.decode.return_value = "Bonjour le monde"
    return tokenizer


@pytest.fixture
def mock_model() -> MagicMock:
    """Fake model that returns a dummy tensor from generate()."""
    model = MagicMock()
    model.generate.return_value = [MagicMock()]
    return model


@pytest.fixture
def translation_service(mock_tokenizer: MagicMock, mock_model: MagicMock) -> TranslationService:
    """TranslationService with one mock language loaded."""
    return TranslationService(
        models={"fr": (mock_tokenizer, mock_model)},
        language_model_mapping={"fr": "Helsinki-NLP/opus-mt-en-fr"},
    )


class TestTranslate:
    """Tests for translate() method."""

    def test_translate_returns_decoded_text(
        self, translation_service: TranslationService, mock_tokenizer: MagicMock, mock_model: MagicMock
    ):
        """translate() calls tokenizer → generate → decode and returns result."""
        result = translation_service.translate("Hello world", "fr")
        assert result == "Bonjour le monde"
        mock_tokenizer.assert_called_once_with("Hello world", return_tensors="pt", padding=True)
        mock_model.generate.assert_called_once()
        mock_tokenizer.decode.assert_called_once()

    def test_translate_unsupported_language_raises(self, translation_service: TranslationService):
        """translate() raises ValueError for unsupported language code."""
        with pytest.raises(ValueError, match="Unsupported Language"):
            translation_service.translate("Hello", "ja")


class TestServiceProperties:
    """Tests for service properties."""

    def test_supported_languages_returns_loaded_keys(self, translation_service: TranslationService):
        """supported_languages returns list of loaded language codes."""
        assert translation_service.supported_languages == ["fr"]

    def test_is_ready_true_when_models_loaded(self, translation_service: TranslationService):
        """is_ready returns True when models dict is not empty."""
        assert translation_service.is_ready is True

    def test_is_ready_false_when_no_models(self):
        """is_ready returns False when models dict is empty."""
        empty_service = TranslationService(models={}, language_model_mapping={})
        assert empty_service.is_ready is False

    def test_empty_service_has_no_languages(self):
        """Service with no models has empty supported_languages."""
        empty_service = TranslationService(models={}, language_model_mapping={})
        assert empty_service.supported_languages == []
