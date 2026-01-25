from enum import StrEnum

from pydantic import Field

from src.core import Dataclass
from src.core.util import Sid, multiline
from src.lib.game.event import Event


class GameStage(StrEnum):
    """Stage of the game lifecycle."""

    WAITING = "waiting"
    ONGOING = "ongoing"
    ENDED = "ended"


class GameState(Dataclass):
    """Internal states of a game.

    This consists of fields that could change during the life cycle of a game.
    Therefore, a lock must be acquired for reading or writing to any field.
    """

    stage: GameStage = Field(
        default=GameStage.WAITING,
        description="Current stage of the game lifecycle.",
    )

    event_queue: list[tuple[int, Sid, Event]] = Field(
        default_factory=list,
        description=multiline(
            """
            Priority queue of upcoming events. Each entry is a (priority, sid,
            event) tuple. Events are stored as Event objects.
            """
        ),
    )

    history: list[Event] = Field(
        default_factory=list,
        description=multiline(
            """
            Record of events at various stages of processing. This list should
            contain enough information to reconstruct the whole game. Events are
            stored as Event objects.
            """
        ),
    )

    default_event_priority: int = Field(
        default=10,
        description=multiline(
            """
            Default priority for events in the event queue. Lower numbers mean
            higher priority.
            """
        ),
    )

    max_react_per_event: int = Field(
        ge=-1,
        description=multiline(
            """
            The default max number of reaction events to any event on the spot,
            which could be overriden for specific events. If 0, no reactions is
            allowed. If -1, the number of reactions is unlimited.
            """
        ),
    )

    max_successive_interrupt: int = Field(
        ge=-1,
        description=multiline(
            """
            The default max number of successive player interruptions allowed to
            be processed in a row, which could be overriden for specific
            speeches. If 0, no interruption is allowed. If -1, the number of
            speech interruptions is unlimited.
            """
        ),
    )
