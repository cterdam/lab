# GPT

**G**eneral Ra**p**id Proto**t**yping.

## Quickstart

### Option 1: Run with Docker

```zsh
make run
```

### Option 2: Run locally

- Create virtual environment
  - `conda create --name <project_name> python=3.12`
  - `conda activate <project_name>`
- Install dependencies
  - `pip install -r requirements.txt`
- Start a Redis server and pass its address in `args`
  - For example: `REDIS_URL=redis://redis:6379/0`
- Run
  - `python -m src`

### View data during run

- Navigate to `localhost:5540`.
- Add a database using the URL `redis:6379`.

## Configure

- Place API keys in `.env`.
- Place other command-line arguments in `args` in the shell format.
  - For example, on each line: `key=value`
- To see all options:
  - `python -m src -h`

## Test

- Run test
  - `make test`

## Cleanup

- Clean pycache and run outputs
  - `make clean`

## Extend

- To add a new arg option:
  - Add a field in `src/core/arguments.py`
  - A CLI arg with the same name will be added automatically.
  - The arg value could be provided via the command line, environmental
    variables, or a `.env` file at repo root, in this order.
  - The parsed value will be in `src.arg`.

- To add a new task:
  - Create dir with `cp -r src/task/dry_run src/task/<new_task_name>`
  - Implement task in `main()` in `src/task/<new_task_name>/main.py`
  - Add an option in the `task` Literal field in `src/core/arguments.py`
  - Add a branching case in `run_task()` in `src/__main__.py`

## Contribute

- Install precommit:
  - `pre-commit install`
- Use [black](https://github.com/psf/black) and
  [isort](https://github.com/PyCQA/isort) for Python files. This is enforced
  with precommit hooks.
- Commit messages should start with tags. E.g. `[model] add Anthropic provider`
