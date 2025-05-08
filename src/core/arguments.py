from typing import Literal

from pydantic import Field

from src.core.data_core import DataCore
from src.core.util import multiline


class Arguments(DataCore):
    """CLI args for the run which are supplied by the user."""

    task: Literal[
        "dry_run",
        "demo",
    ] = Field(
        default="demo",
        description=multiline(
            """
            Task to perform. All tasks are implemented under src/task.
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
