.PHONY: test build run stop logs clean release

# ── Development ──────────────────────────────

test:
	pytest tests/ -v --cov=src --cov-report=term-missing

lint:
	python -m py_compile src/main.py
	@echo "✅ Syntax OK"

# ── Docker ───────────────────────────────────

build:
	docker compose build

run:
	docker compose up -d

stop:
	docker compose down

logs:
	docker compose logs -f --tail=50

restart:
	docker compose restart

health:
	@docker inspect --format='{{.State.Health.Status}}' horitas-bot 2>/dev/null || echo "Container not running"

# ── Docker with Admin ────────────────────────

run-admin:
	docker compose -f docker-compose.yml -f docker-compose.admin.yml up -d

stop-admin:
	docker compose -f docker-compose.yml -f docker-compose.admin.yml down

# ── Release ──────────────────────────────────

release:
	@if [ -z "$(VERSION)" ]; then echo "❌ Usage: make release VERSION=1.0.0"; exit 1; fi
	git tag v$(VERSION)
	git push --tags
	@echo "✅ Tag v$(VERSION) pushed — GitHub Actions will build and publish to ghcr.io"

# ── Cleanup ──────────────────────────────────

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache/ .coverage htmlcov/
