# GPT

**G**eneral Ra**p**id Proto**t**yping.

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
- Each logger instance has a `logspace` and a `logname`.
  - The `logspace` is a list representing the hierarchy of names passed on by
    ancestor classes.
  - The `logname` is unique within its `logspace`.
- Each logger keeps its own log files under `out/{run_id}/log`.
  - The location of its log files depend on its `logspace` and `logid`.
- At the end of the run, each logger emits all its counters in its logs and in a
  JSON file aside its log files.
