"""Core of the app - loads huggingface model and translates text."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

import structlog
from transformers.models.marian import MarianMTModel, MarianTokenizer

from lang_api.core.config import Settings
from lang_api.core.metrics import MODEL_LOAD_DURATION, TRANSLATION_DURATION, TRANSLATION_REQUESTS

logger = structlog.stdlib.get_logger(__name__)


@dataclass
class TranslationService:
    """Loads and runs Huggingface translation models, keyed by language code."""

    models: dict[str, tuple[MarianTokenizer, MarianMTModel]]
    language_model_mapping: dict[str, str]

    @staticmethod
    def load_models(settings: Settings) -> TranslationService:
        """Load all translation models from settings.

        Args:
            settings (Settings): Application settings with language to model mapping.

        Returns:
            TranslationService: Service with all models loaded.
        """
        models = {}
        logger.info("Loading translation models...")
        for lang, model_id in settings.supported_languages.items():
            logger.info("Loading model %s for %s", model_id, lang)
            with MODEL_LOAD_DURATION.labels(language=lang).time():
                tokenizer = MarianTokenizer.from_pretrained(model_id)
                model = MarianMTModel.from_pretrained(model_id)
            models[lang] = (tokenizer, model)
        logger.info("Models loaded: %s", list(settings.supported_languages.keys()))
        return TranslationService(models=models, language_model_mapping=settings.supported_languages)

    def translate(self, text: str, target_language: str) -> str:
        """Translate english text to target language.

        Args:
            text (str): English text to translate.
            target_language (str): ISO language code.

        Returns:
            str: Translated text

        Raises:
            ValueError: If target_language is not supported
        """
        if target_language not in self.models:
            raise ValueError(f"Unsupported Language {target_language}")

        logger.info("Translating to %s (%d chars)", target_language, len(text))

        tokenizer, model = self.models[target_language]

        with TRANSLATION_DURATION.labels(target_language=target_language).time():
            inputs = tokenizer(text, return_tensors="pt", padding=True)
            outputs = model.generate(input_ids=inputs["input_ids"])
            result = cast(str, tokenizer.decode(outputs[0], skip_special_tokens=True))
            TRANSLATION_REQUESTS.labels(target_language=target_language).inc()

        logger.info(
            "Translation complete", input_chars=len(text), output_chars=len(result), target_language=target_language
        )
        return result

    @property
    def supported_languages(self) -> list[str]:
        """Retrieve supported language codes.

        Returns:
            list[str]: list of supported languages
        """
        return list(self.models.keys())

    @property
    def is_ready(self) -> bool:
        """Whether models are loaded.

        Returns:
            bool: True if loaded False if not.
        """
        return len(self.models) > 0
