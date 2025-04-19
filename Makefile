.PHONY: test

test:
	pytest

run:
	python -m src

clean:
	rm -rf out/*
