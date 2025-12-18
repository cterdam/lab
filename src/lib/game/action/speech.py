from pydantic import Field

from src.core import Dataclass, logid


class Speech(Dataclass):
    """In-game speech from a player to other players."""

    speaker: logid
