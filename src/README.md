# Developer's Guide

## Style

- Use absolute imports.
- Always apply the most minimal fix feasible.
- Variable names should be one word where possible.
- Each word should preferrably be one syllable.
- Only when something is truly a composite concept should its name be more than
  one word.
- When applicable, use abbreviations. For example. `src` for "source".
- Do not write duplicate code. If some code elsewhere already solves the
  problem, reuse it to the extent possible.
- If something only has a small, fixed set of options, make it an enum. If
  something has strong type requirements, make it a Pydantic Dataclass.
- READMEs should document things that are not obvious from reading the code.
  Avoid enumerating facts that are already clear from signatures, types, or
  defaults (e.g. listing every argument with its type). Focus on the "why",
  non-obvious interactions, and gotchas.

## Core

- The arguments are accessible with `from src import arg`. This contains
  user-supplied arguments and shouldn't be changed.
- Other run-centric variables are accessible with `from src import env`.
- The root logger is accessible with `from src import log`. Use it with
  `log.info(msg)`.

## Logging

- To print something, use logging.
  - This can be achieved by using logging methods on a `Logger` object such as
    `src.log`
  - Each logger can also keep concurrency-safe counters.
- To log an object, use `env.repr()` to format it.
- One logical message = one log call. Never split a message across multiple
  log calls. If the message has multiple parts (e.g. a summary and details),
  construct a single multi-line string and log it in one call.

### Loggers

- Each logger instance has a `logspace` and a `logname`.
  - The `logspace` is a list representing the hierarchy of names passed on by
    ancestor classes.
  - The `logname` is unique within its `logspace`.
  - The `lid` is produced from the `logspace` and `logname` and is unique
    across the run.
  - The `logspace` and `logname` determine the location in `out/$RUN_ID/log`
    where the logger instance dumps its logs.

### Severity

- Use the following logging severities:
  - `TRACE` -> Routine information that the user otherwise already knows.
  - `DEBUG` -> Important details on the function call level.
  - `INFO` -> Important details on the app level.
  - `SUCCESS` -> The success of an operation that could otherwise have failed.
  - `WARNING` -> Unexpected outcomes that are non-fatal.
  - `ERROR` -> Unexpected outcomes that cause a non-essential function to fail.
  - `CRITICAL` -> Unexpected outcomes that cause the entire app to fail.

### Groups

- Each group has a `gid` which is also used as the Redis key for the group.
- Groups can contain any string ID, such as `lid` or other `gid`.
- Membership in a group is represented by a real number. A negative value is
  exclusion.

### Serial ID

- The serial ID is an ever-increasing number ID.

### Error Counters

When a runtime error is detected but handled gracefully (e.g. a missing lid,
a type mismatch), increment an error counter instead of raising. This makes
errors visible in counter dumps without crashing the program.

- Define error counter keys in the class's `_coke` enum, using
  `obj_id(env.ERR_COKE_PREFIX, "<error_name>")` as the value.
- Increment with `self.incr(self.coke.ERR_...)` at the point of detection.
- Log a `warning` alongside the increment to provide context.

## Redis

- The codebase uses Redis as a single source of truth.
- The collection of all alive loggers is accessible via `env.lids`.
- The counters of each logger are collected under its own hash.
- Each module might include a `coke` module which contains its COunter KEys.

## Arguments

All arguments are defined as fields in `src/core/arguments.py`. They are
resolved in the following priority order (highest wins):

1. **CLI flags** — `--task=algo`
2. **Environment variables** — in `.env`
3. **Args file** — in the `args` file at repo root
4. **Defaults** — the `default` value in each `Field()`

In practice, most arguments are set in `args`. API keys go in `.env`.

### How arguments reach the container

The `args` file is baked into the Docker image at build time (`COPY . .`).
The `.env` file is loaded at runtime via `env_file: .env` in `compose.yml`.

Some arguments may have infrastructure side effects beyond the Python process
(e.g. a host path that needs bind-mounting into the container). These are
extracted from `args` by the `Makefile` and exported as environment variables
for `docker compose`. When adding such an argument, update the `Makefile` and
`compose.yml` accordingly.

## Tasks

Each task lives in `src/task/<name>/` and exposes a `main()` function.
The dispatcher in `src/__main__.py` dynamically imports `src.task.<arg.task>`
and calls `main()`. Each task directory contains its own `README.md`.

## Extend

- To add a new arg option:
  - Add a field in `src/core/arguments.py`
  - An arg with the same name will be added automatically.
  - The arg value could be provided in `.env` or `args` at repo root.
  - The parsed value will be accessible from `src.arg`
  - If the arg has infrastructure side effects (e.g. a host path that needs
    mounting), also update the `Makefile` and `compose.yml`.

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

## Other

- If you call an async coroutine in the task main function, it can only involve
  1 event loop. Otherwise, cached redis clients will be obsolete.
