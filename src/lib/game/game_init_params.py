from pydantic import Field

from src.core import Dataclass
from src.core.util import multiline


class GameInitParams(Dataclass):
    """Config params for a game."""

    chat_allowed: bool = Field(
        description=multiline(
            """
            If True, players could speak to react to any in-game event. If
            False, players could only speak when the game requires them to.
            """
        ),
    )

    chat_interrupt_allowed: bool = Field(
        description=multiline(
            """
            If True, players could interrupt each other's speeches. If False,
            speeches will go un-interrupted.
            """
        ),
    )
