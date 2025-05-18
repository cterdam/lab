from pydantic import BaseModel, ConfigDict


class DataCore(BaseModel):
    """Base dataclass with strict guarantees and handy properties."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        validate_assignment=True,
        validate_default=True,
    )

    def __str__(self) -> str:
        from src import env

        return env.repr(self)
