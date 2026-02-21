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

1. Game: Streamline event stages: combine handled and final, they shouldn't be
   separate stages. Each event should just have TENTATIVE, PROCESSING, FINAL.
2. Game: make event visibility include and exclude groups. These groups are
   present in game.gona and will be used to decide who can see an event vs not,
   when handling evens and getting reactions, etc.
3. Game: add some more coke for various types of events in game

4. Algo: Add doc instructions in the root README about what Algo can do, and in
   src/README about the steps for adding a new Algo, similar to how the steps
   for adding a new task is documented in README
5. Algo: Remove the magic number in AswanNormal by making normal distribution
   lookup a service in src/lib/model/ (is there a common python pkg for this?)

- type validation: beartype, typeguard, deal
- Loguru PR
  - Similar issue: <https://github.com/empicano/aiomqtt/issues/52>
  - Almost all asyncio objects are not thread safe:
    <https://docs.python.org/3/library/asyncio-dev.html>
