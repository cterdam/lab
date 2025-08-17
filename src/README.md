# Developer's Guide

## Core

- The arguments are accessible with `from src import arg`. This contains
  user-supplied arguments and shouldn't be changed.
- Other run-centric variables are accessible with `from src import env`.
- The root logger is accessible with `from src import log`. Use it with
  `log.info(msg)`.

## Logging

- When trying to print something, use logging.
- When trying to printing an object, use `env.repr()` to format it.
- Each logger can also keep concurrency-safe counters.

## Redis

- The codebase uses Redis as a single source of truth.
- The collection of all loggers is under `env.LOGID_SET_KEY`.
- The counters of each logger are collected under its own hash.
- Each module might include a `coke` module which contains its COunter KEys.

## Extend

- To add a new arg option:
  - Add a field in `src/core/arguments.py`
  - An arg with the same name will be added automatically.
  - The arg value could be provided in `.env` or `args` at repo root.
  - The parsed value will be accessible from `src.arg`

- To add a new task:
  - Create task dir with `cp -r src/task/dry_run src/task/<new_task_name>`
  - Implement task in `main()` in `src/task/<new_task_name>/main.py`
  - Add an option in the `task` Literal field in `src/core/arguments.py`

## Contribute

- Install precommit:
  - `pre-commit install`
- Use [black](https://github.com/psf/black) and
  [isort](https://github.com/PyCQA/isort) for Python files. This is enforced
  with precommit hooks.
- Commit messages should start with tags. E.g. `[model] add Anthropic provider`
