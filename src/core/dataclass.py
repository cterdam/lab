from pydantic import ConfigDict
from redis_om import Field, JsonModel

from src.core.util import sid_t


def _get_next_sid() -> sid_t:
    """Get the next serial ID from the environment."""
    from src import env

    return env.next_sid()


class Dataclass(JsonModel):
    """Base dataclass with strict guarantees and Redis persistence."""

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        validate_default=True,
    )

    sid: sid_t = Field(
        default_factory=_get_next_sid,
        primary_key=True,
        description="Serial ID, auto generated monotonically increasing.",
    )

    def __str__(self) -> str:
        from src.core.util import prepr

        return prepr(self)
