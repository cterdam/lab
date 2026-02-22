.SILENT:
.PHONY: run test clean

define launch
	NAME=$$(grep -sh '^run_name=' .env args | head -1 | cut -d= -f2-) && \
	NAME=$${NAME:-$$(LC_ALL=C tr -dc a-z0-9 < /dev/urandom | head -c4)} && \
	export RUN_ID="$$NAME-$$(date -u +%y%m%d-%H%M%S)" && \
	docker compose -p $$RUN_ID up -d redis --quiet-pull >/dev/null 2>&1 && \
	export REDIS_INSIGHT=$$(docker compose -p $$RUN_ID port redis 8001) && \
	docker compose -p $$RUN_ID up --build $(1) -d --quiet-pull >/dev/null 2>&1 && \
	docker logs -f $$(docker compose -p $$RUN_ID ps -aq $(1)); \
	docker compose -p $$RUN_ID rm -f $(1) >/dev/null 2>&1
endef

test:
	$(call launch,test)

run:
	$(call launch,app)

clean:
	docker compose ls -q | xargs -I{} docker compose -p {} down -v 2>/dev/null; true
	docker network prune -f 2>/dev/null; true
	rm -rf out/*
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
	find . -depth -type d -name ".mypy_cache" -exec rm -r "{}" +
	find . -depth -type d -name ".pytest_cache" -exec rm -r "{}" +
