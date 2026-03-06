"""Dependency injection for API routes."""

from typing import Annotated

from fastapi import Depends, Request

from lang_api.models.services import TranslationService


def get_translation_service(request: Request) -> TranslationService:
    """Retrieve the Translation Service from app state.

    Args:
        request (Request): Incoming API request.

    Returns:
        TranslationService: The loaded translation service.
    """
    return request.app.state.translation_service


TranslationServiceDep = Annotated[TranslationService, Depends(get_translation_service)]  # Shortcut for long type
