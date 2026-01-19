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

## Groups

Redis-backed group membership with include/exclude rules.

Groups are identified by gid (group ID) in format `g:groupname`. The prefix and
separator are configurable in env (`GID_PREFIX`, `GID_SEPARATOR`).

### Redis Keys

```
g:{name}/include       # SET of included logids or gids
g:{name}/exclude       # SET of excluded logids or gids
```

Groups are implicit - they exist if they have members.

### Usage

```python
from src.lib.data import group

# Add members (groups are created implicitly)
group.add_include("admins", "player:alice")
group.add_include("users", "player:bob")
group.add_include("users", group.gid("admins"))  # Include admins group

# Query membership
group.get_members("users")  # {"player:alice", "player:bob"}
group.is_member("player:alice", "users")  # True
```

### Resolution

1. Collect included members (direct + from included groups, recursively)
2. Collect excluded members (direct + from excluded groups)
3. Return `included - excluded` (excludes always win)

Circular references are detected and logged as warnings.

## Logging

- Logs are timed by UTC.
- Each logger keeps its own log files under `out/$RUN_ID/log`.
- At the end of the run, each logger emits all its counters in its logs and in a
  JSON file aside its log files.

## Contribute

- AddPlayer event
  - Group access ctrl for players
  - Different player groups inside state

- Loguru PR
  - Similar issue: <https://github.com/empicano/aiomqtt/issues/52>
  - Almost all asyncio objects are not thread safe:
    <https://docs.python.org/3/library/asyncio-dev.html>

- random number generator obj
- set random seeds
- ttt game

- type validation: beartype, typeguard, deal
