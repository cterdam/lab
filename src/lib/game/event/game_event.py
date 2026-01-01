from typing import TypeAlias

from pydantic import Field

from src.core import Dataclass, logid
from src.core.util import multiline
from src.lib.data.serial import Serial

geid_t: TypeAlias = int
_geids = Serial(logname="game_event_ids")


class GameEvent(Dataclass):
    """In-game event."""

    geid: geid_t = Field(
        description="Event ID which is sorted by creation time.",
        default_factory=_geids.next,
    )

    blocks: list[geid_t] = Field(
        default_factory=list,
        description=multiline(
            """
            If this event is a reaction, this is the list of GEIDs of events that
            this event is reacting to.
            """
        ),
    )

    requires: list[geid_t] = Field(
        default_factory=list,
        description=multiline(
            """
            If this event has reactions, this is the list of GEIDs of reactions
            that must be fully processed before this event can finish processing.
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
