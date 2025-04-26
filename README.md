# GenAI Best Practices

Template Python repo for GenAI projects.

## Setup

- Create virtual environment
  - `conda create --name <project_name> python=3.12`
  - `conda activate <project_name>`
- Install dependencies
  - `pip install -r requirements.txt`
- Install precommit:
  - `pre-commit install`

## Run

- Run main program
  - `make run`

- See all runnable tasks
  - `python -m src -h`

## Test

- Run test
  - `make test`

## Cleanup

- Run cleanup script
  - `make clean`

## Extend

- Steps to add a new task:
  - Create dir with `cp -r src/tasks/dry_run src/tasks/<new_task_name>`
  - Implement task in `main()` in `src/tasks/<new_task_name>/main.py`
  - Add an option in the `task` Literal in `src/core/config.py`
  - Add routing logic in `run_task()` in `src/__main__.py`

## Contribute

- The pre-commit hooks ensure code is formatted with
  [black](https://github.com/psf/black) before submitting.  This helps by
  producing the smallest possible diff.
- Commit messages should start with tags. E.g. `[model] add Anthropic provider`
