"""Unit tests for config.py."""

import pytest
from pydantic_settings import SettingsError

from lang_api.core.config import Settings


class TestSettingsDefaults:
    """Tests for Settings default values."""

    def test_default_supported_languages(self):
        """Default config loads fr, de, es with correct Helsinki-NLP model IDs."""
        settings = Settings()
        assert settings.supported_languages == {
            "fr": "Helsinki-NLP/opus-mt-en-fr",
            "de": "Helsinki-NLP/opus-mt-en-de",
            "es": "Helsinki-NLP/opus-mt-en-es",
        }

    def test_model_cache_dir_defaults_to_none(self):
        """Cache dir defaults to None, deferring to HuggingFace default."""
        settings = Settings()
        assert settings.model_cache_dir is None

    def test_debug_defaults_to_false(self):
        """Debug mode is off by default."""
        settings = Settings()
        assert settings.debug is False


class TestSettingsEnvOverride:
    """Tests for environment variable overrides."""

    def test_env_overrides_supported_languages(self, monkeypatch: pytest.MonkeyPatch):
        """LANGAPI_SUPPORTED_LANGUAGES env var overrides default languages."""
        monkeypatch.setenv(
            "LANGAPI_SUPPORTED_LANGUAGES",
            '{"ja": "Helsinki-NLP/opus-mt-en-ja"}',
        )
        settings = Settings()
        assert settings.supported_languages == {"ja": "Helsinki-NLP/opus-mt-en-ja"}

    def test_env_overrides_cache_dir(self, monkeypatch: pytest.MonkeyPatch):
        """LANGAPI_MODEL_CACHE_DIR env var sets custom cache path."""
        monkeypatch.setenv("LANGAPI_MODEL_CACHE_DIR", "/tmp/models")
        settings = Settings()
        assert settings.model_cache_dir == "/tmp/models"

    def test_debug_enabled_via_env(self, monkeypatch: pytest.MonkeyPatch):
        """Debug mode can be enabled via LANGAPI_DEBUG."""
        monkeypatch.setenv("LANGAPI_DEBUG", "true")
        settings = Settings()
        assert settings.debug is True

    def test_invalid_supported_languages_format_raises(self, monkeypatch: pytest.MonkeyPatch):
        """Non-JSON string for supported_languages raises ValidationError."""
        monkeypatch.setenv("LANGAPI_SUPPORTED_LANGUAGES", "not-valid-json")
        with pytest.raises(SettingsError):
            Settings()


class TestSettingsEdgeCases:
    """Tests for edge case configurations."""

    def test_empty_supported_languages_is_valid(self, monkeypatch: pytest.MonkeyPatch):
        """Empty dict is valid — service starts with no languages."""
        monkeypatch.setenv("LANGAPI_SUPPORTED_LANGUAGES", "{}")
        settings = Settings()
        assert settings.supported_languages == {}
