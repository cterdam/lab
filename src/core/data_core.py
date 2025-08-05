from pydantic import BaseModel, ConfigDict


class DataCore(BaseModel):
    """Base dataclass with strict guarantees and handy properties."""

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        validate_default=True,
    )

    def __str__(self) -> str:
        from src.core.dutil import prepr

        return prepr(self)
