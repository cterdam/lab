.ONESHELL:
.SILENT:
.PHONY: run test clean

test:
	set -euo pipefail
	export COMPOSE_PROJECT_NAME="lab-test-$$(head -c 4 /dev/urandom | xxd -p)"
	export REDIS_UI_PORT=0
	trap 'docker compose down -v >/dev/null 2>&1' EXIT INT TERM
	docker compose up --build test -d --quiet-pull >/dev/null 2>&1
	echo "Redis UI: http://localhost:$$(docker compose port redis 8001 | cut -d: -f2)"
	docker logs -f $$(docker compose ps -q test)
	docker compose down -v >/dev/null 2>&1

run:
	set -euo pipefail
	export COMPOSE_PROJECT_NAME="lab-run-$$(head -c 4 /dev/urandom | xxd -p)"
	export REDIS_UI_PORT=0
	trap 'docker compose down -v >/dev/null 2>&1' EXIT INT TERM
	docker compose up --build app -d --quiet-pull >/dev/null 2>&1
	echo "Redis UI: http://localhost:$$(docker compose port redis 8001 | cut -d: -f2)"
	docker logs -f $$(docker compose ps -q app)
	docker compose down -v >/dev/null 2>&1

clean:
	rm -rf out/*
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
	find . -depth -type d -name ".mypy_cache" -exec rm -r "{}" +
	find . -depth -type d -name ".pytest_cache" -exec rm -r "{}" +
