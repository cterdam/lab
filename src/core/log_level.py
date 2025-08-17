from pydantic import Field
from pydantic_extra_types.color import Color

from src.core.dataclass import Dataclass


class LogLevel(Dataclass):
    """Log level."""

    name: str = Field(
        min_length=1,
        description="Name of the logging level as its unique identifier",
    )

    no: int = Field(
        ge=1,
        description="Positive integer severity of the logging level.",
    )

    color: Color = Field(
        description="Color for the level's header in logs.",
    )
