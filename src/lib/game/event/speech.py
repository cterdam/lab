from pydantic import Field

from src.core import logid_t
from src.core.util import multiline
from src.lib.game.event.game_event import GameEvent


class Speech(GameEvent):
    """In-game talk from a player to other players."""

    audience: list[logid_t] = Field(description="Listeners of this speech.")
    content: str = Field(description="Content of the speech.")


class Interrupt(Speech):
    """A speech to interrupt another speech."""

    target_speech_content: str = Field(
        description=multiline(
            """
            The partial content of the target speech that was successfully
            delivered before interruption.
            """
        ),
    )
