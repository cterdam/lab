from typing import Literal

from pydantic import ConfigDict, Field, computed_field

from src.core.data_core import DataCore
from src.core.util import multiline


class Arguments(DataCore):
    """CLI args for the run which are supplied by the user."""

    # Arguments should not change after parsing
    model_config = ConfigDict(frozen=True)

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
