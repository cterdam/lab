import pathlib

from src.core.strict_data import StrictData


class Context(StrictData):
    """Run-level dynamic context info."""

    # Dir to hold all outputs of the current run
    out_dir: pathlib.Path = None  # pyright:ignore
