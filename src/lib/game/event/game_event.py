from enum import StrEnum
from typing import Any

from pydantic import Field, model_validator

from src.core import Dataclass, logid
from src.core.util import multiline, sid_t

SerializedGameEvent = dict[str, Any]


class GameEventStage(StrEnum):
    """Stage of an event in its lifecycle."""

    TENTATIVE = "tentative"
    HANDLING = "handling"
    HANDLED = "handled"
    FINAL = "final"


class GameEvent(Dataclass):
    """In-game event."""

    kind: str | None = Field(
        default=None,
        description=multiline(
            """
            The class name of this event type, relevant for deserialization.
            Automatically set to the class name if not provided.
            """,
        ),
    )

    @model_validator(mode="before")
    @classmethod
    def set_kind(cls, data):
        """Ensure kind is always set to the class name."""
        if isinstance(data, dict) and data.get("kind") is None:
            data["kind"] = cls.__name__
        return data

    stage: GameEventStage = Field(
        default=GameEventStage.TENTATIVE,
        description="Current stage of the event in its lifecycle.",
    )

    blocks: list[sid_t] = Field(
        default_factory=list,
        description=multiline(
            """
            If this event is a reaction, this is the list of GEIDs of events that
            this event is reacting to.
            """
        ),
    )

    requires: list[sid_t] = Field(
        default_factory=list,
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
        description=multiline(
            """
            List of player logids who can see this event. If None, the event is
            visible to all players. If empty list, the event is visible to no
            players.
            """
        ),
    )
