from pydantic import Field

from src.core import Dataclass
from src.core.util import multiline


class GameState(Dataclass):
    """Internal states of a game."""

    ongoing: bool = Field(
        description="True iff the game is still ongoing.",
    )

    max_react_per_event: int = Field(
        ge=-1,
        description=multiline(
            """
            The default max number of reaction events to any event on the spot,
            which could be overriden for specific events. If 0, no reactions is
            allowed. If -1, the number of reactions is unlimited.
            """
        ),
    )

    max_successive_interrupt: int = Field(
        ge=-1,
        description=multiline(
            """
            The default max number of successive player interruptions allowed to
            be processed in a row, which could be overriden for specific
            speeches. If 0, no interruption is allowed. If -1, the number of
            speech interruptions is unlimited.
            """
        ),
    )
