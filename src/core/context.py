import pathlib

from src.core.strict_data import StrictData


class Context(StrictData):
    """Run-level dynamic context info."""

    # Directory to hold all output of the current run
    out_dir: pathlib.Path | None = None

    # Directory to hold all logs of the current run
    log_dir: pathlib.Path | None = None
