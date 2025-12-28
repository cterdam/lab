from uuid import UUID, uuid4

from pydantic import Field

from src.core import Dataclass, logid
from src.core.util import multiline


class Event(Dataclass):
    """In-game event."""

    event_id: UUID = Field(
        description="UUID of this event.",
        default_factory=uuid4,
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
