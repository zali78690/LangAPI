"""API route handlers for translation endpoint."""

from fastapi import APIRouter

from lang_api.api.dependencies import TranslationServiceDep
from lang_api.api.schemas import (
    HealthResponse,
    LanguagesResponse,
    TranslationRequest,
    TranslationResponse,
)

router = APIRouter()


@router.post("/api/v1/translate", response_model=TranslationResponse)
def translate(request: TranslationRequest, service: TranslationServiceDep) -> TranslationResponse:
    """Translate English text to target language.

    Args:
        request (TranslationRequest): Translation request body.
        service (TranslationServiceDep): Injected translation service.

    Returns:
        TranslationResponse: Translated text with metadata.
    """
    translated = service.translate(request.text, request.target_language)
    return TranslationResponse(
        translated_text=translated,
        target_language=request.target_language,
    )


@router.get("/api/v1/languages", response_model=LanguagesResponse)
def get_languages(service: TranslationServiceDep) -> LanguagesResponse:
    """List supported translation languages.

    Args:
        service (TranslationServiceDep): Injected translation service.

    Returns:
        LanguagesResponse: Available language codes and model IDs.
    """
    return LanguagesResponse(
        supported_languages={
            lang: f"Helsinki-NLP/opus-mt-en-{lang}" for lang in service.supported_languages
        }  # TODO: Store the original supported_languages dict on the service
    )


@router.get("/health", response_model=HealthResponse)
def health(service: TranslationServiceDep) -> HealthResponse:
    """Check service health and model readiness.

    Args:
        service (TranslationServiceDep): Injected translation service.

    Returns:
        HealthResponse: Service status information.
    """
    return HealthResponse(
        status="healthy" if service.is_ready else "unhealthy",
        models_loaded=service.is_ready,
        supported_languages=service.supported_languages,
    )
