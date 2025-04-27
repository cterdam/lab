from typing import Literal

from pydantic import Field

from src.core.strict_data import StrictData
from src.core.util import multiline


class Config(StrictData):
    """User-supplied static run config."""

    task: Literal[
        "dry_run",
        "content_gen",
    ] = Field(
        default="dry_run",
        description=multiline(
            """
            Task to perform. All tasks are implemented under src/tasks.
            """,
        ),
    )

    run_name: str | None = Field(
        default=None,
        description=multiline(
            """
            Name of the current run which will also used as output dir under
            `out/`. If empty, a unique run name will be generated in its place.
            """
        ),
    )
