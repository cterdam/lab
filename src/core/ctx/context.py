import pathlib

from pydantic import BaseModel


class Context(BaseModel):
    """Run-level context info."""

    outdir: pathlib.Path = None  # pyright: ignore
