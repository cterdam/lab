import pathlib

from src.core.config import Config


class RunContext(Config):
    """Run-level dynamic context info."""

    # Dir to hold all outputs of the current run
    out_dir: pathlib.Path = None  # pyright:ignore
