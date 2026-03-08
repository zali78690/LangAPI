# LangAPI

RESTful API serving Helsinki-NLP translation models for English to French, German, and Spanish.

## Overview

LangAPI is a translation API built with FastAPI and HuggingFace's MarianMT models. It serves translations via a REST interface with auto-generated OpenAPI documentation.

## Features

- Translate English text to French, German, or Spanish
- Interactive API docs at `/docs` (Swagger UI)
- Health check endpoint for monitoring and readiness
- Input validation with clear error messages
- Structured JSON logging (structlog) with console mode for development
- Request correlation IDs (X-Request-ID) for tracing
- Prometheus metrics endpoint (`/metrics`) for production monitoring

## Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.12+ | Language |
| FastAPI | Web framework |
| HuggingFace transformers | Model loading and inference |
| Helsinki-NLP/opus-mt | MarianMT translation models |
| structlog | Structured logging (JSON/console) |
| prometheus-fastapi-instrumentator | Prometheus metrics |
| pydantic-settings | Configuration management |
| uv | Package management |
| ruff | Formatting and linting |
| pyright | Static type checking |

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- ~1GB disk space for model downloads (cached after first run)

## Quick Start

```bash
git clone https://github.com/zali78690/LangAPI.git
cd LangAPI
uv sync
uv run uvicorn lang_api.main:app
```

The first startup downloads three translation models (~300MB each). Subsequent startups use the cached models.

Once running, visit http://localhost:8000/docs for the interactive Swagger UI.

## API Endpoints

| Method | Path | Description | Status Codes |
|--------|------|-------------|--------------|
| `POST` | `/api/v1/translate` | Translate English text to target language | 200, 400, 422, 500 |
| `GET` | `/api/v1/languages` | List supported languages and model IDs | 200 |
| `GET` | `/health` | Service health and model readiness | 200 |
| `GET` | `/metrics` | Prometheus metrics (not in OpenAPI) | 200 |

### Example: Translate text

```bash
curl -X POST http://localhost:8000/api/v1/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, my name is Zain.", "target_language": "fr"}'
```

Response:

```json
{
  "translated_text": "Salut, mon nom est Zain.",
  "source_language": "en",
  "target_language": "fr"
}
```

## Configuration

Settings are loaded from environment variables with the `LANGAPI_` prefix.

| Variable | Description | Default |
|----------|-------------|---------|
| `LANGAPI_SUPPORTED_LANGUAGES` | JSON dict of language codes to model IDs | `{"fr": "Helsinki-NLP/opus-mt-en-fr", "de": "Helsinki-NLP/opus-mt-en-de", "es": "Helsinki-NLP/opus-mt-en-es"}` |
| `LANGAPI_MODEL_CACHE_DIR` | Override HuggingFace model cache directory | `None` (uses HF default) |
| `LANGAPI_DEBUG` | Enable console-formatted logs for development | `False` |

## Project Structure

```
lang_api/
  main.py                  # Thin entrypoint for uvicorn
  core/
    app.py                 # App factory, lifespan, exception handlers
    config.py              # pydantic-settings configuration
    logging.py             # Structured logging configuration (structlog)
    metrics.py             # Prometheus metrics definitions and setup
  models/
    services.py            # TranslationService — model loading and inference
  api/
    routes.py              # API endpoint handlers
    schemas.py             # Pydantic request/response models
    dependencies.py        # FastAPI dependency injection
    middleware.py           # Request logging and correlation ID middleware
decision_records/        # Architecture Decision Records (YAML)
tests/
  conftest.py              # Shared fixtures (mock services, test client)
  api/
    test_routes.py         # Endpoint integration tests
    test_middleware.py      # Request logging middleware tests
    test_schemas.py        # Pydantic schema validation tests
  core/
    test_config.py         # Settings and env var tests
    test_logging.py        # Structlog configuration tests
    test_metrics.py        # Prometheus metrics tests
  models/
    test_services.py       # TranslationService unit tests
```

## Docker

Build the image (first build downloads models, ~2 min):

```bash
docker build -t langapi .
```

Run the container:

```bash
docker run -p 8000:8000 langapi
```

Override settings via environment variables:

```bash
docker run -p 8000:8000 -e LANGAPI_DEBUG=true langapi
```

The image uses a multi-stage build that pre-downloads all translation models at build time. This gives ~5s startup (vs ~60s without pre-caching). Image size is ~2.5GB due to PyTorch and 3 translation models.

## Development

Install dev dependencies and set up pre-commit hooks:

```bash
uv sync --group dev
uv run pre-commit install
```

Run the API in development mode (auto-reloads on code changes):

```bash
uv run uvicorn lang_api.main:app --reload
```

Run code quality checks:

```bash
ruff format .           # Format code
ruff check .            # Lint
ruff check --fix .      # Lint with auto-fix
pyright                 # Type check
```

Run tests:

```bash
uv run pytest
```

