"""Application settings and configurations."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from LANGAPI_ environment variables."""

    supported_languages: dict[str, str] = {lang: f"Helsinki-NLP/opus-mt-en-{lang}" for lang in ("fr", "de", "es")}
    model_cache_dir: str | None = None
    debug: bool = False
    model_config = SettingsConfigDict(env_prefix="LANGAPI_")
