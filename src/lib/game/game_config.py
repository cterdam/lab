from pydantic import Field

from src.core import Dataclass
from src.core.util import multiline


class GameConfig(Dataclass):
    """Config options for a game."""

    max_speech_per_event: int = Field(
        ge=-1,
        description=multiline(
            """
            The default max number of player speeches allowed in reaction to any
            event. This default could be overriden for specific events. If 0, no
            chat is allowed. If -1, the number of player speeches is unlimited.
            """
        ),
    )

    max_interrupt_per_speech: int = Field(
        ge=-1,
        description=multiline(
            """
            The default max number of player interruptions allowed in reaction
            to any other player speech. This default could be overriden for
            specific speeches. If 0, no interruption is allowed. If -1, the
            number of speech interruptions is unlimited.
            """
        ),
    )
