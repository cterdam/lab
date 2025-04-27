# GPT

**G**eneral Ra**p**id Proto**t**yping.

## Setup

- Create virtual environment
  - `conda create --name <project_name> python=3.12`
  - `conda activate <project_name>`
- Install dependencies
  - `pip install -r requirements.txt`
- Install precommit:
  - `pre-commit install`

## Run

- Run task
  - `python -m src --task=<task_name>`

- See all options
  - `python -m src -h`

## Test

- Run test
  - `make test`

## Cleanup

- Clean pycache and run outputs
  - `make clean`

## Extend

- To add a new config option:
  - Add a field in `src/core/config.py`
  - A CLI arg with the same name will be added automatically.
    The parsed value will be in `cfg`.

- To add a new task:
  - Create dir with `cp -r src/tasks/dry_run src/tasks/<new_task_name>`
  - Implement task in `main()` in `src/tasks/<new_task_name>/main.py`
  - Add an option in the `task` Literal field in `src/core/config.py`
  - Add a branching case in `run_task()` in `src/__main__.py`

## Contribute

- Use [black](https://github.com/psf/black) and
  [isort](https://github.com/PyCQA/isort) for Python files. This is enforced
  with precommit hooks.
- Commit messages should start with tags. E.g. `[model] add Anthropic provider`
