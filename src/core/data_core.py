from pydantic import BaseModel, ConfigDict


class DataCore(BaseModel):
    """Base dataclass with strict guarantees and handy properties."""

    model_config = ConfigDict(
        validate_default=True,
        validate_assignment=True,
        extra="forbid",
    )

    def __str__(self) -> str:
        from src import env

        return env.repr(self)
