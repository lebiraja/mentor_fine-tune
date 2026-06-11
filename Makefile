.PHONY: models up down build logs test test-smoke dev clean

# One-time model download (~4 GB total). Needs HF_TOKEN in .env only for gated repos (none currently).
models:
	bash scripts/download_models.sh

up:
	docker compose up -d --build

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f --tail=100

# Unit + protocol tests (fake engines, fast)
test:
	docker compose run --rm --no-deps backend pytest -q

# Smoke tests against real ONNX models (needs `make models` first)
test-smoke:
	docker compose run --rm --no-deps backend pytest -q -m smoke

# Frontend dev server (vite) against a running backend
dev:
	cd frontend && npm run dev

clean:
	docker compose down -v --remove-orphans
