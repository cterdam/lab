from enum import StrEnum

from pydantic import Field

from src.core import Dataclass, Gid, Lid, Sid
from src.core.util import multiline


class EventStage(StrEnum):
    """Stage of an event in its lifecycle."""

    TENTATIVE = "tentative"
    PROCESSING = "processing"
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

    vis: dict[Lid | Gid, float] = Field(
        default_factory=dict,
        description=multiline(
            """
            Visibility group for this event. Maps Gid or Lid to weights, same
            format as group membership. Resolved like group.resolve():
            sub-groups are expanded with weight propagation, and direct entries
            override indirect ones. Only resolved Lids with positive weight can
            see the event. Empty dict means visible to no one.
            """
        ),
    )
