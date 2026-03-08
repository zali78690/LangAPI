"""Unit tests for schemas.py."""

import pytest
from pydantic import ValidationError

from lang_api.api.schemas import (
    ErrorResponse,
    HealthResponse,
    LanguagesResponse,
    TranslationRequest,
    TranslationResponse,
)


@pytest.mark.parametrize(
    "text, should_pass",
    [
        ("hello", True),
        ("a" * 5000, True),
        ("a" * 5001, False),
        ("", False),
        ("héllo 世界", True),
        ("   ", False),
    ],
    ids=["valid", "at_5000_limit", "over_5000_limit", "empty", "unicode", "whitespace_only"],
)
def test_translation_request_text_validation(text: str, should_pass: bool):
    """Tests to stress test input request validation for translation service."""
    if should_pass:
        request = TranslationRequest(text=text, target_language="fr")
        assert request.text == text
    else:
        with pytest.raises(ValidationError):
            TranslationRequest(text=text, target_language="fr")


@pytest.mark.parametrize(
    "code, should_pass",
    [
        ("fr", True),
        ("f", False),
        ("fra", False),
    ],
    ids=["valid_2char", "too_short", "too_long"],
)
def test_translation_request_language_code_validation(code: str, should_pass: bool):
    """Language code must be exactly 2 characters."""
    if should_pass:
        request = TranslationRequest(text="Hello", target_language=code)
        assert request.target_language == code
    else:
        with pytest.raises(ValidationError):
            TranslationRequest(text="hello", target_language=code)


def test_translation_response_defaults_source_language():
    """Source language defaults to 'en' when not provided."""
    response = TranslationResponse(translated_text="Bonjour", target_language="fr")
    assert response.source_language == "en"


def test_languages_response_accepts_valid_data():
    """LanguagesResponse accepts language-to-model mapping."""
    response = LanguagesResponse(
        supported_languages={"fr": "Helsinki-NLP/opus-mt-en-fr", "de": "Helsinki-NLP/opus-mt-en-de"}
    )
    assert response.supported_languages == {"fr": "Helsinki-NLP/opus-mt-en-fr", "de": "Helsinki-NLP/opus-mt-en-de"}


def test_languages_response_empty_dict():
    """LanguagesResponse accepts empty dict."""
    response = LanguagesResponse(supported_languages={})
    assert response.supported_languages == {}


def test_health_response_accepts_valid_data():
    """HealthResponse accepts well-formed data."""
    response = HealthResponse(
        status="healthy",
        models_loaded=True,
        supported_languages=["fr", "de"],
    )
    assert response.status == "healthy"
    assert response.models_loaded is True
    assert response.supported_languages == ["fr", "de"]


def test_health_response_empty_languages():
    """HealthResponse accepts empty supported languages list."""
    response = HealthResponse(status="unhealthy", models_loaded=False, supported_languages=[])
    assert response.supported_languages == []


def test_error_response_accepts_valid_data():
    """ErrorResponse accepts well-formed error data."""
    response = ErrorResponse(error="bad_request", detail="Unsupported Language ja")
    assert response.error == "bad_request"
    assert response.detail == "Unsupported Language ja"
