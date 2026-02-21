# **L**arge **A**gile **B**ox

## You should use a monorepo

This is the repo for all of your prototyping experiments.

A monorepo solves the diamond dependency problem. A good codebase is reusable.

## Quickstart

### Setup

- Install Docker and start the Docker daemon.
- Create a `.env` file even if empty.

### Run

- To start a run: `make run`.
- To visualize data from the most recent run, navigate to `localhost:8001`

### Configure

- Place API keys in `.env`.
- Place other CLI arguments in `args` in the shell format.
  - On each line: `key=value`

### Other

- To run tests: `make test`
- To clean pycache and run outputs: `make clean`

## Logging

- Logs are timed by UTC.
- Each logger keeps its own log files under `out/$RUN_ID/log`.
- At the end of the run, each logger emits all its counters in its logs and in a
  JSON file aside its log files.

## Contribute

- Loguru PR
  - Similar issue: <https://github.com/empicano/aiomqtt/issues/52>
  - Almost all asyncio objects are not thread safe:
    <https://docs.python.org/3/library/asyncio-dev.html>

- Game: merge event stages handled and final, they shouldn't be separate
- Game: make event visibility include and exclude groups
- Game: add some more coke

- Algo: Add doc instructions in the root README about what Algo can do, and in
  src/README about the steps for adding a new Algo, similar to how the steps for
  adding a new task is documented in README
- Algo: Remove the magic number in AswanNormal by making normal distribution
  lookup a service in src/lib/data/ (is there a common python pkg for this?)

- random number generator obj
- set random seeds
- ttt game

- type validation: beartype, typeguard, deal
