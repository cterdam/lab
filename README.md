# **G**eneral Ra**p**id Proto**t**yping

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

- Remove Logger LogLevel

- Simplify can react count cap to just count with max
- AddPlayer event
  - Group access ctrl for players
  - Different player groups inside state

- Game save & load
  - Including dumping Redis counters

- Loguru PR
  - Similar issue: <https://github.com/empicano/aiomqtt/issues/52>
  - Almost all asyncio objects are not thread safe:
    <https://docs.python.org/3/library/asyncio-dev.html>

- random number generator obj
- set random seeds
- ttt game

- type validation: beartype, typeguard, deal
