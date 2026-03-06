"""Unit tests for services.py."""

from unittest.mock import MagicMock

import pytest

from lang_api.core.metrics import TRANSLATION_DURATION, TRANSLATION_REQUESTS
from lang_api.models.services import TranslationService


class TestTranslate:
    """Tests for translate() method."""

    def test_translate_returns_decoded_text(
        self, mock_translation_service: TranslationService, mock_tokenizer: MagicMock, mock_model: MagicMock
    ):
        """translate() calls tokenizer -> generate -> decode and returns result."""
        result = mock_translation_service.translate("Hello world", "fr")
        assert result == "Bonjour le monde"
        mock_tokenizer.assert_called_once_with("Hello world", return_tensors="pt", padding=True)
        mock_model.generate.assert_called_once()
        mock_tokenizer.decode.assert_called_once()

    def test_translate_unsupported_language_raises(self, mock_translation_service: TranslationService):
        """translate() raises ValueError for unsupported language code."""
        with pytest.raises(ValueError, match="Unsupported Language"):
            mock_translation_service.translate("Hello", "ja")


class TestServiceProperties:
    """Tests for service properties."""

    def test_supported_languages_returns_loaded_keys(self, mock_translation_service: TranslationService):
        """supported_languages returns list of loaded language codes."""
        assert mock_translation_service.supported_languages == ["fr"]

    def test_is_ready_true_when_models_loaded(self, mock_translation_service: TranslationService):
        """is_ready returns True when models dict is not empty."""
        assert mock_translation_service.is_ready is True

    def test_is_ready_false_when_no_models(self, empty_translation_service: TranslationService):
        """is_ready returns False when models dict is empty."""
        assert empty_translation_service.is_ready is False

    def test_empty_service_has_no_languages(self, empty_translation_service: TranslationService):
        """Service with no models has empty supported_languages."""
        assert empty_translation_service.supported_languages == []


class TestTranslationMetrics:
    """Tests for Prometheus metrics in translate()."""

    def test_translate_increments_counter(self, mock_translation_service: TranslationService) -> None:
        """translate() increments translation_requests_total counter."""
        # prometheus_client has no public read API for counters; _value.get() is the standard workaround
        before = TRANSLATION_REQUESTS.labels(target_language="fr")._value.get()
        mock_translation_service.translate("Hello", "fr")
        after = TRANSLATION_REQUESTS.labels(target_language="fr")._value.get()
        assert after == before + 1

    def test_translate_records_duration(self, mock_translation_service: TranslationService) -> None:
        """translate() records duration in histogram."""
        # prometheus_client has no public read API for histograms; _sum.get() is the standard workaround
        before = TRANSLATION_DURATION.labels(target_language="fr")._sum.get()
        mock_translation_service.translate("Hello", "fr")
        after = TRANSLATION_DURATION.labels(target_language="fr")._sum.get()
        assert after > before
