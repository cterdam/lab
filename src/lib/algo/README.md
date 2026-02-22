# Algo

Experiment with algorithmic computations in a standardized interface. The
framework provides built-in execution timing, logging, and metrics collection.

## Run

- Run an algo with arguments: `task=algo` and `algo=<import_path>`
- Algos are discovered at runtime via their import path, specified with the
  `algo` argument (e.g. `algo=src.lib.algo.aswan.AswanNormal`).
- Input parameters used by algos are generic arguments found in `src.arg`.

## Extend

- To add a new algo:
  - Create algo dir under `src/lib/algo/<algo_name>/`
  - Define `Input`, `Output`, and base `Algo` subclass in
    `src/lib/algo/<algo_name>/<algo_name>.py`
  - Create one or more implementations that inherit from the base and implement
    `async def _run(self, inp) -> Output`
  - Export classes in `src/lib/algo/<algo_name>/__init__.py`
  - Add any new input parameters as fields in `src/core/arguments.py`
