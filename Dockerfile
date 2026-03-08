# ---- Stage 1: Builder ----
FROM python:3.12-slim AS builder

WORKDIR /app

# Install uv package manager
RUN pip install --no-cache-dir uv

# Copy dependency files first (layer caching)
COPY pyproject.toml uv.lock ./

# Install production dependencies only
RUN uv sync --frozen --no-dev

# Copy application code (needed for model pre-download script)
COPY lang_api/ lang_api/

# Pre-download all translation models into /app/model-cache
# Uses LANGAPI_MODEL_CACHE_DIR so Settings.model_cache_dir is the single source of truth
ENV LANGAPI_MODEL_CACHE_DIR=/app/model-cache
RUN .venv/bin/python -c "\
from lang_api.core.config import Settings; \
from transformers.models.marian import MarianMTModel, MarianTokenizer; \
s = Settings(); \
[(MarianTokenizer.from_pretrained(m, cache_dir=s.model_cache_dir), MarianMTModel.from_pretrained(m, cache_dir=s.model_cache_dir)) for m in s.supported_languages.values()]; \
print('All models downloaded')"

# ---- Stage 2: Runtime ----
FROM python:3.12-slim

WORKDIR /app

# Create non-root user
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid 1000 -ms /bin/bash appuser

# Copy virtualenv and model cache from builder
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv
COPY --from=builder --chown=appuser:appuser /app/model-cache /app/model-cache

# Copy application code
COPY --chown=appuser:appuser lang_api/ lang_api/

# Configure environment
ENV PATH="/app/.venv/bin:$PATH"
ENV LANGAPI_MODEL_CACHE_DIR=/app/model-cache

# Switch to non-root user
USER appuser

EXPOSE 8000

CMD ["uvicorn", "lang_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
