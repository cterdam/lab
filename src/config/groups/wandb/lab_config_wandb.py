"""Config about logging."""

from typing import List
from pydantic import Field

from src.config.lab_config_base import LabConfigBase
from src.util.general import multiline

__all__ = [
    "LabConfigWandb",
]


class LabConfigWandb(LabConfigBase):
    """Config about W&B."""

    login_entity: str | None = Field(
        default=None,
        description=multiline(
            """
            Username or team name for wandb. If unset, will be default entity associated
            with login credentials.
            """
        ),
    )

    save_code: bool = Field(
        default=True,
        description="If true, saves all `.py` source code files in repo on wandb.",
    )

    run_group: str | None = Field(
        default=None,
        description="Optional group name for the run on wandb.",
    )

    run_tags: List[str] = Field(
        default=[],
        description="Optional tags for the run on wandb.",
    )

    run_notes: str | None = Field(
        default=None,
        description="Optional notes for the run on wandb.",
    )

    capture_console: bool = Field(
        default=True,
        description="If true, captures stdout and stderr output to wandb logs.",
    )

    tabulate_logs: bool = Field(
        default=True,
        description="If true, uses a wandb Table to store log msgs.",
    )
