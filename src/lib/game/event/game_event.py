from typing import TypeAlias

from pydantic import Field

from src.core import Dataclass, logid
from src.core.util import multiline
from src.lib.data.serial import Serial

geid: TypeAlias = int
_geids = Serial(logname="game_event_ids")


class GameEvent(Dataclass):
    """In-game event."""

    event_id: geid = Field(
        description="Event ID which is sorted by creation time.",
        default_factory=_geids.next,
    )

    react_to: geid | None = Field(
        default=None,
        description=multiline(
            """
            If this event is a reaction, this is the GEID of the event that
            this event is reacting to.
            """
        ),
    )

    src: logid = Field(
        description=multiline(
            """
            Source of this event. If the event is a speech, this is the speaker.
            If the event is a battle, this is the attacker. If the event is
            environmental and external to any player, this is the game's logid.
            """
        ),
    )

    announce_before: bool = Field(
        default=True,
        description=multiline(
            """
            True iff this event should be announced for reaction before it is
            handled.
            """
        ),
    )

    announce_after: bool = Field(
        default=True,
        description=multiline(
            """
            True iff this event should be announced for reaction after it is
            handled.
            """
        ),
    )

    visible: list[logid] | None = Field(
        default=None,
        description=multiline(
            """
            List of player logids who can see this event. If None, the event is
            visible to all players. If empty list, the event is visible to no
            players.
            """
        ),
    )
