from enum import StrEnum

from redis_om import Field

from src.core import Dataclass, logid
from src.core.util import multiline, sid_t


class GameEventStage(StrEnum):
    """Stage of an event in its lifecycle."""

    TENTATIVE = "tentative"
    HANDLING = "handling"
    HANDLED = "handled"
    FINAL = "final"


class GameEvent(Dataclass):
    """In-game event."""

    stage: GameEventStage = Field(
        default=GameEventStage.TENTATIVE,
        description="Current stage of the event in its lifecycle.",
    )

    blocks: list[sid_t] = Field(
        default_factory=list,
        index=False,
        description=multiline(
            """
            If this event is a reaction, this is the list of GEIDs of events that
            this event is reacting to.
            """
        ),
    )

    requires: list[sid_t] = Field(
        default_factory=list,
        index=False,
        description=multiline(
            """
            If this event has reactions, this is the list of GEIDs of reactions
            that must be fully processed before this event can finish processing.
            """
        ),
    )

    src: logid | None = Field(
        default=None,
        description=multiline(
            """
            Source of this event. If the event is a speech, this is the speaker.
            If the event is a battle, this is the attacker. If the event is
            environmental and external to any player, this is the game's logid.
            If None, will be set to the game's logid when the game adds it to
            the event queue.
            """
        ),
    )

    visible: list[logid] | None = Field(
        default=None,
        index=False,
        description=multiline(
            """
            List of player logids who can see this event. If None, the event is
            visible to all players. If empty list, the event is visible to no
            players.
            """
        ),
    )
