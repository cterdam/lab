from datetime import timedelta

from pydantic import Field

from src.core.dataclass import Dataclass


class FuncResult(Dataclass):
    """Result of a function call.

    To be subclassed to include more fields.
    """

    duration: timedelta = Field(
        description="Duration of the model generation.",
    )
