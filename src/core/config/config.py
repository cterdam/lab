from pydantic import BaseModel, ConfigDict, Field

from src.core.util.general import multiline


class Config(BaseModel):
    """User-supplied static run config."""

    model_config = ConfigDict(
        validate_default=False,
        validate_assignment=True,
        extra="forbid",
    )

    run_name: str = Field(  # pyright:ignore
        default=None,
        description=multiline(
            """
            Name of the current run which will also used as output dir under
            `out/`. If empty, a unique run name will be generated in its place.
            """
        ),
    )
