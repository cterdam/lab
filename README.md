# GPT

**G**eneral Ra**p**id Proto**t**yping.

## Quickstart

- Install Docker.
- To start a run: `make run`.
- To visualize data from a run, navigate to `localhost:8001`

## Configure

- Place API keys in `.env`
- Place other command-line arguments in `args` in the shell format.
  - On each line: `key=value`

## Other

- To run tests: `make test`
- To clean pycache and run outputs: `make clean`

## Extend

- To add a new arg option:
  - Add a field in `src/core/arguments.py`
  - A CLI arg with the same name will be added automatically.
  - The arg value could be provided via the CLI or in `.env` at repo root.
  - The parsed value will be in `src.arg`

- To add a new task:
  - Create dir with `cp -r src/task/dry_run src/task/<new_task_name>`
  - Implement task in `main()` in `src/task/<new_task_name>/main.py`
  - Add an option in the `task` Literal field in `src/core/arguments.py`

## Contribute

- Install precommit:
  - `pre-commit install`
- Use [black](https://github.com/psf/black) and
  [isort](https://github.com/PyCQA/isort) for Python files. This is enforced
  with precommit hooks.
- Commit messages should start with tags. E.g. `[model] add Anthropic provider`
