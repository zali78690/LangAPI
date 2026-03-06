"""Defines the shape of requests and responses for the API."""

from pydantic import BaseModel, Field, field_validator


class TranslationRequest(BaseModel):
    """Request body for translation request."""

    text: str = Field(min_length=1, max_length=5000, description="The text to be translated.")
    target_language: str = Field(min_length=2, max_length=2, description="Language ISO code e.g., 'en' for English.")

    @field_validator("text")
    @classmethod
    def reject_whitespace_only(cls, value: str):
        """Reject whitespace only text."""
        if not value.strip():
            raise ValueError("Text must contain non-whitespace characters.")
        return value


class TranslationResponse(BaseModel):
    """Response body for translation endpoint."""

    translated_text: str = Field(description="The translated text.")
    source_language: str = Field(default="en", description="Source language ISO code")
    target_language: str = Field(description="Target language ISO code e.g., 'fr' for French.")


class LanguagesResponse(BaseModel):
    """Response body for supported languages endpoint."""

    supported_languages: dict[str, str] = Field(description="Language codes mapped to model IDs")


class HealthResponse(BaseModel):
    """Response body for health check endpoint."""

    status: str = Field(description="Service health status")
    models_loaded: bool = Field(description="Whether translation models are loaded")
    supported_languages: list[str] = Field(description="Available language codes")


class ErrorResponse(BaseModel):
    """Response body for error responses."""

    error: str = Field(description="Error type identifier")
    detail: str = Field(description="Human-readable error message")
