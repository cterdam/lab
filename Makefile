.ONESHELL:
.SILENT:
.PHONY: run test clean

test:
	set -euo pipefail
	trap 'docker compose down test >/dev/null 2>&1' EXIT INT TERM
	docker compose down -v >/dev/null 2>&1
	docker compose up --build test -d --quiet-pull >/dev/null 2>&1
	docker logs -f $$(docker compose ps -q test)
	docker compose down test >/dev/null 2>&1

run:
	set -euo pipefail
	trap 'docker compose down app >/dev/null 2>&1' EXIT INT TERM
	docker compose down -v >/dev/null 2>&1
	docker compose up --build app -d --quiet-pull >/dev/null 2>&1
	docker logs -f $$(docker compose ps -q app)
	docker compose down app >/dev/null 2>&1

clean:
	rm -rf out/*
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
	find . -depth -type d -name ".mypy_cache" -exec rm -r "{}" +
	find . -depth -type d -name ".pytest_cache" -exec rm -r "{}" +
