.PHONY: install test format lint type-check check clean docker-build docker-up docker-down docker-logs

install:
	uv sync --group dev

test:
	uv run pytest

format:
	uv run ruff format .

lint:
	uv run ruff check .

type-check:
	uv run pyright

check: format lint type-check test

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache

docker-build:
	docker build -t langapi .

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f
