# 🧑‍💻 Lab source code

## 🎖️ Getting started

- Start by (from repo root) running `python -m src`. This runs `src/__main__.py`.

- For each run, any local outputs are collected in the configurated out dir.
  - The default out dir is (from repo root) `out/<project_name>/<run_name>/`.
  - If an alternative out dir is configured, any outputs will be in `<out_dir>/`.


## 🛠️ config

- The config includes a number of groups, each containing a number of options.
  - `python -m src -h` to see all configurable options.

- Each group is stored in a subdir of `src/config/groups/`. Within each such subdir:
  - Each group sets a schema in `lab_config_{group_name}.py`.
  - Any yaml file in `all/` satisfying its schema is a valid source.
  - The source name is the file's base name, without the `.yaml` extension.

- `src/config/select.yaml` selects a default source name for each group.

- Each option in each group necessarily has a value at runtime. These are decided with
  the [precedence](#precedence) of config values.

- At runtime, after command-line [parsing](#parsing), the `src.config` module exports an
  object, `config`, which is a `LabConfig` and contains the final value of all options.

### Precedence

Even though each config option necessarily has a value at runtime, all command line
arguments are optional. This is because these values can still come from other places.
In decreasing levels of precedence, these are:

- Run-time command-line argument `--<group_name>/<option_name> <value>`
  - **This has the highest precedence.**

- Source selected via a command-line argument `--<group_name> <source_name>`

- Source selected in `src/config/select.yaml`

- Default value provided in the group's schema class
  - **This has the lowest precedence.**

### Parsing

- During argparse, each option is available as a command-line argument.

- Any option not set via command-line arguments has the value of `None` in argparse,
  which is used to prevent it from overwriting the value taken from other sources.

- All values are taken as strings and parsed into expected types in the same way `yaml`
  parses strings into Python objects. Therefore:
  - In order to set an option to `None`, the input should be `null`.
  - In order to set an option to the string `null`, the input should be `\"null\"`.
  - In order to force a numeric string to be string, the input should be surrounded with
    quotation marks.

- Config options are processed after parsing, a processed called scaffolding.
  - In this process, their values could change.
  - The config table exported via logging provide config values after scaffolding.
  - With `--dry-run`, configs are exported directly after parsing, without scaffolding.

### Adding a new group

- Make the subdir `src/config/groups/<new_group_name>`. In it:
  - `lab_config_<new_group_name>.py` should define the schema.
    - This needs to subclass `LabConfigBase`.
  - `all/` contains at least one yaml file which satisfies the schema.
    - There should be a `default.yaml` which just writes `{}`, so it uses the
      default value set in the schema for all options.

- In `src/config/lab_config.py`, modify `LabConfig`.
  - Add the `<new_group_name>` field.
  - Add the `<new_group_name>_source` field.
    - Register it to the field validator for the `expand_path` method.
  - Modify the `__init__` method to initialize the `<new_group_name>` field.

- Modify `src/config/select.yaml` to select a source for this new group.

And that's it!

### Adding a new option within an existent group

- Modify the group schema to add the new option as a field.
  - If it can only take a few values, use `Literal` or other Pydantic verification
    schemes.
  - If this is a shell variable, its default factory should fetch it from shell.

- If this value necessitates postprocessing, modify `src/config/scaffold.py`.

And that's it!

## 🪵 log

- Logs can appear at a number of destinations:
  - Stdout
  - Local log file `log.txt` in out dir
  - Wandb
- All log entry timestamps are in UTC.

### Best logging practices

- There should not be any print statements. Always use the logger instead.

- To log msgs, simply `from src.log import logger` and use `logger` as in `loguru`.

- Use logging levels this way:
  - `trace` - trivial msgs which are predictable given other logs; e.g. config setup.
  - `debug` - debug msgs about latent variables; e.g. system snapshots.
  - `info` - normal default logs; e.g. the overall config table.
  - `success` - a costly or uncertain action succeedes; e.g. downloading an artifact, or
    detecting some shell env var.
  - `warning` - errors that don't damage the program's functionalities; e.g. detecting a
    strange config setup.
  - `error` - errors that force the program to prune functionalities but can still
    continue.
  - `critical` - errors that force the program to abort. e.g. not enough disk space.

- The timing of logging:
  - For quick actions, log *after* it's completed, rather than *before*.
    - For example, if a piece of code creates a file system directory, log `"Directory
      created"` rather than `"About to create directory"`. Log msgs should give
      unambiguous interpretations as much as they can.
  - For slow actions, log both *before* and *after*, and optionally log progress
    halfway.

### Logging on wandb

- To use wandb logging, the `WANDB_API_KEY` shell variable must be set with a valid API
  key.
- Logs will appear under the given run name and project name in the wandb entity chosen
  with the API key.
- The run ID on wandb will also be the same as the run name.
- The job type of the wandb run will be the same as the task in the config.
- By default, all `.py` files in the repo at this time of the run will also be saved in
  the wandb run as an artifact.

## 🧮 data

## 📐 eval

## 🪆 model

## 🚂 train

## 🔗 util
