"""Application entry for uvicorn."""

from lang_api.core.app import create_app

app = create_app()
