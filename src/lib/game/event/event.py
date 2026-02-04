from enum import StrEnum

from pydantic import Field

from src.core import Dataclass, Lid
from src.core.util import Sid, multiline


class EventStage(StrEnum):
    """Stage of an event in its lifecycle."""

    TENTATIVE = "tentative"
    HANDLING = "handling"
    HANDLED = "handled"
    FINAL = "final"


class Event(Dataclass):
    """In-game event."""

    stage: EventStage = Field(
        default=EventStage.TENTATIVE,
        description="Current stage of the event in its lifecycle.",
    )

    blocks: list[Sid] = Field(
        default_factory=list,
        description=multiline(
            """
            If this event is a reaction, this is the list of GEIDs of events that
            this event is reacting to.
            """
        ),
    )

    requires: list[Sid] = Field(
        default_factory=list,
        description=multiline(
            """
            If this event has reactions, this is the list of GEIDs of reactions
            that must be fully processed before this event can finish processing.
            """
        ),
    )

    src: Lid | None = Field(
        default=None,
        description=multiline(
            """
            Source of this event. If the event is a speech, this is the speaker.
            If the event is a battle, this is the attacker. If the event is
            environmental and external to any player, this is the game's lid.
            If None, will be set to the game's lid when the game adds it to
            the event queue.
            """
        ),
    )

    visible: list[Lid] | None = Field(
        default=None,
        description=multiline(
            """
            List of player lids who can see this event. If None, the event is
            visible to all players. If empty list, the event is visible to no
            players.
            """
        ),
    )
