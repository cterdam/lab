import pathlib

from pydantic import ConfigDict, Field

from src.core.config import Config
from src.core.util import multiline


class RunContext(Config):
    """Run-level dynamic context info."""

    # Override Config to disable validating default values.
    model_config = ConfigDict(
        validate_default=False,
        validate_assignment=True,
        extra="forbid",
    )

    out_dir: pathlib.Path = Field(
        default=None,  # pyright:ignore
        description=multiline(
            """
            Dir to hold all outputs of the current run.
            """
        ),
    )
