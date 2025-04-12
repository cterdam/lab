# Python Best Practices

Template Python repo.

## Setup

- Create virtual environment
  - `conda create --name <project_name> python=3.12`
  - `conda activate <project_name>`
- Install dependencies
  - `pip install -r requirements.txt`
- Install precommit:
  - `pre-commit install`

## Test

- Run test
  - `make test`

## Contribute

- The pre-commit hooks ensure code is formatted with
  [black](https://github.com/psf/black) before submitting.  This helps by
  producing the smallest possible diff.
- Commit messages should start with tags. E.g. `[model] add Anthropic provider`
