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
ENV HF_HOME=/app/model-cache
RUN .venv/bin/python -c "\
from transformers.models.marian import MarianMTModel, MarianTokenizer; \
models = ['Helsinki-NLP/opus-mt-en-fr', 'Helsinki-NLP/opus-mt-en-de', 'Helsinki-NLP/opus-mt-en-es']; \
[(MarianTokenizer.from_pretrained(m), MarianMTModel.from_pretrained(m)) for m in models]; \
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
ENV HF_HOME=/app/model-cache
ENV LANGAPI_DEBUG=false

# Switch to non-root user
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "lang_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
