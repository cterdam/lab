from datetime import timedelta

from pydantic import Field

from src.core.dataclass import Dataclass
from src.core.util import multiline


class FuncResult(Dataclass):
    """Result of a function call.

    To be subclassed to include more fields.
    """

    duration: timedelta = Field(
        description=multiline(
            """
            Duration of the model generation.
            """
        ),
    )
