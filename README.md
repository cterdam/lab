# 💈 Lab

Lab (**L**anguage **A**I **B**uilding) allows you to systematically manage many
runs of training and evaluation of language models.

## 🏁 Setup

```zsh
conda create -n lab python=3.12
conda activate lab
pip install -r requirements.txt
```

## 🕹️ Use 

- `python -m src` to directly start using the default configs.
  - Add `-h` to see all configurable options.
  - Add `--dry-run` to print out configured option values and exit.
- By default, a log file will be created at `out/<project_name>/<run_name>/log.txt`.
- The run will also be logged on wandb. Make sure the `WANDB_API_KEY` shell variable is
  set.

## TODO

- Use wandb table? Probably cannot work real-time. If so, get rid of existing logic
- Fix typecheck with assignments of None values
- Rewrite logging level explanation as markdown table
- random config: torch.utils.deterministic.fill_uninitialized_memory
- Serialize logs into json file
- Add special sinks for logging metrics
    - Needs to be numbers and cannot retroactively change
    - When logging, explicitly supply timestep number
    - Write into text log and also wandb if turned on
    - Write into metrics json log
        (To be used to graph)
        - Organize: both one file each metric, and aggregate by timestep
        - Automatically rewritten upon each change
        - Include metadata about metrics (mean, max, std)
- use typer for an app-like interface?
- use hash of config to compare config
- use rich for config table
- change log file separator to tabulate chars
- postprocessing including log saving upon exit - use `atexit`
- during teardown, for traceback display: either `rich` or `loguru.catch`
- Snapshot env
    - python ver, libraries ver, git hash and any uncommitted edits, username, host
    - torch devices, ram, disk space
- progress bar - use `rich`
- collect summary (of metrics) from run, just like how wandb does
- see if wandb.magic will work once other wandb components are complete
- resume a run, both on and off wandb
- compute SHA256 sum of each model and write a file when uploading
- use trogon to add `tui` command for help
