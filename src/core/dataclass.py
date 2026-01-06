from pydantic import BaseModel, ConfigDict, Field

from src.core.util import next_sid, prepr, sid_t


class Dataclass(BaseModel):
    """Base dataclass with strict guarantees and handy properties.

    All instances have a serial ID (sid) field that is automatically generated.
    """

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        validate_default=True,
    )

    sid: sid_t = Field(
        default_factory=next_sid,
        description="Serial ID, auto generated monotonically increasing.",
    )

    def __str__(self) -> str:
        return prepr(self)
