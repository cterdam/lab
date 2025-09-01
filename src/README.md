# Developer's Guide

## Core

- The arguments are accessible with `from src import arg`. This contains
  user-supplied arguments and shouldn't be changed.
- Other run-centric variables are accessible with `from src import env`.
- The root logger is accessible with `from src import log`. Use it with
  `log.info(msg)`.

## Logging

- When trying to print something, use logging.
  - This can be achieved by using logging methods on a `Logger` object such as
    `src.log`
  - Each logger can also keep concurrency-safe counters.
- When trying to printing an object, use `env.repr()` to format it.

### Loggers

- Each logger instance has a `logspace` and a `logname`.
  - The `logspace` is a list representing the hierarchy of names passed on by
    ancestor classes.
  - The `logname` is unique within its `logspace`.
  - The `logid` is produced from the `logspace` and `logname` and is unique
    across the run.
  - The `logspace` and `logname` determine the location in `out/$RUN_ID/log`
    where the logger instance dumps its logs.

### Severity

- Use the following logging severities:
  - `TRACE` -> Routine information that the user otherwise already knows.
  - `DEBUG` -> Important details that could be useful for debugging.
  - `INFO` -> Information that is meaningful not on the function execution level
        but on the app level.
  - `SUCCESS` -> The success of an operation that could otherwise have failed.
  - `WARNING` -> Unexpected outcomes that are non-fatal.
  - `ERROR` -> Unexpected outcomes that cause an operation to fail.
  - `CRITICAL` -> Unexpected outcomes that cause the entire app run to fail.

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
