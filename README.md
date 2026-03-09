# LangAPI

RESTful API serving Helsinki-NLP translation models for English to French, German, and Spanish.

## Overview

LangAPI is a translation API built with FastAPI and HuggingFace's MarianMT models. It serves translations via a REST interface with auto-generated OpenAPI documentation.

Key architectural decisions are documented as [Architecture Decision Records](decision_records/) (YAML format), split into [implemented](decision_records/implemented/) and [proposed](decision_records/proposed/) decisions.

## Features

- Translate English text to French, German, or Spanish
- Interactive API docs at `/docs` (Swagger UI)
- Health check endpoint for monitoring and readiness
- Input validation with clear error messages
- Structured JSON logging (structlog) with console mode for development
- Request correlation IDs (X-Request-ID) for tracing
- Prometheus metrics endpoint (`/metrics`) for production monitoring
- Pre-configured Grafana dashboard with request rate, latency, and language distribution panels
- Dockerised deployment with multi-stage build and model pre-caching

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
| Docker | Containerised deployment |
| Prometheus | Metrics scraping and storage |
| Grafana | Pre-configured monitoring dashboard |

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- [Docker](https://docs.docker.com/get-docker/) (for containerised deployment and monitoring stack)
- ~1GB disk space for model downloads when running locally (cached after first run). Running via Docker container requires ~5GB on disk — see [Resource Requirements](#resource-requirements)

## Quick Start

```bash
git clone https://github.com/zali78690/LangAPI.git
cd LangAPI
uv sync
uv run uvicorn lang_api.main:app
```

The first startup downloads three translation models (~300MB each). Subsequent startups use the cached models.

Once running, visit http://localhost:8000/docs for the interactive Swagger UI.

Run the test suite (does not require model downloads):

```bash
uv run pytest
```

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
| `LANGAPI_MODEL_CACHE_DIR` | Model cache directory (passed to `from_pretrained(cache_dir=...)`) | `None` (uses HuggingFace default `~/.cache/huggingface`) |
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
monitoring/
  prometheus/
    prometheus.yml         # Scrape config (langapi:8000 every 15s)
  grafana/
    provisioning/          # Datasource, dashboard provider, dashboard JSON
decision_records/
  implemented/             # Decisions currently in the codebase
  proposed/                # Future improvements with concrete approaches
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
Dockerfile               # Multi-stage build with model pre-download
docker-compose.yml       # App + Prometheus + Grafana stack
Makefile                 # Dev/ops command shortcuts
```

## Docker (API Only)

Run just the translation API without monitoring. Use this for quick testing or when you don't need Prometheus/Grafana.

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

The image uses a multi-stage build that pre-downloads all translation models at build time. This gives ~5s startup (vs ~60s without pre-caching).

### Resource Requirements

| Resource | Requirement | Notes |
|----------|-------------|-------|
| Disk (image) | ~5GB | CPU-only PyTorch + 3 translation models + HuggingFace cache + Python deps |
| RAM | ~2GB | ~600MB per loaded model + PyTorch runtime overhead |
| CPU | 1+ cores | Inference is CPU-bound; more cores = faster under concurrent load |

## Monitoring Stack (API + Prometheus + Grafana)

Run the API with the full observability stack. Use this when you want to explore metrics and dashboards.

Start the full stack:

```bash
docker compose up --build
```

First build takes ~5-10 minutes (downloading models). Subsequent runs use the cached image — just `docker compose up` (no `--build`). You only need `--build` again if you change the Dockerfile, dependencies, or application code. Monitoring config changes are picked up automatically (mounted as volumes).

| Service | URL | Purpose |
|---------|-----|---------|
| API docs | http://localhost:8000/docs | Swagger UI |
| Metrics (raw) | http://localhost:8000/metrics | Prometheus text format |
| Prometheus | http://localhost:9090 | Metrics scraping and queries |
| Grafana dashboard | http://localhost:3000/d/langapi/langapi | Pre-configured panels (no login needed) |

### Test the flow

1. Visit http://localhost:3000/d/langapi/langapi — Grafana opens with no login, "LangAPI" dashboard visible
2. Make some translation requests via http://localhost:8000/docs (or curl)
3. Wait ~15s (Prometheus scrape interval)
4. Refresh Grafana — panels populate with data

The Grafana dashboard ("LangAPI") is pre-configured with 4 panels:
request rate, translation latency (p50/p95/p99), requests by language, and model load time.

Grafana runs with anonymous authentication enabled — no login required. This is intentional for local development; in production you would restrict access at the ingress/reverse-proxy level.

Stop the stack:

```bash
docker compose down
```

## Development

Install dev dependencies and set up pre-commit hooks:

```bash
make install
uv run pre-commit install
```

Run the API in development mode (auto-reloads on code changes):

```bash
uv run uvicorn lang_api.main:app --reload
```

### Make Targets

| Target | Purpose |
|--------|---------|
| `make install` | Install all dependencies (including dev) |
| `make test` | Run test suite |
| `make format` | Format code with ruff |
| `make lint` | Lint code with ruff |
| `make type-check` | Static type checking with pyright |
| `make check` | Run all quality gates (format + lint + type-check + test) |
| `make clean` | Remove `__pycache__`, `.pytest_cache`, `.ruff_cache` |
| `make docker-build` | Build Docker image |
| `make docker-up` | Start monitoring stack (detached) |
| `make docker-down` | Stop monitoring stack |
| `make docker-logs` | Follow container logs |

