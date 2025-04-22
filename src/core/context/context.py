import pathlib

from pydantic import BaseModel, ConfigDict


class Context(BaseModel):
    """Run-level dynamic context info."""

    model_config = ConfigDict(
        validate_default=False,
        validate_assignment=True,
        extra="forbid",
    )

    out_dir: pathlib.Path = None  # pyright: ignore
