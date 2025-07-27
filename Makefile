.ONESHELL:
.SILENT:
.PHONY: run test clean

test:
	pytest -n auto

run:
	set -euo pipefail
	trap 'docker compose down >/dev/null 2>&1' EXIT INT TERM
	docker compose build -q
	docker compose up -d --quiet-pull >/dev/null 2>&1
	docker logs -f $$(docker compose ps -q app)

clean:
	rm -rf out/*
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
	find . -depth -type d -name ".mypy_cache" -exec rm -r "{}" +
	find . -depth -type d -name ".pytest_cache" -exec rm -r "{}" +
