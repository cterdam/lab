from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.core.util import multiline, next_sid, prepr, sid_t


class Dataclass(BaseModel):
    """Base dataclass with strict guarantees and handy properties.

    All instances have a serial ID (sid) field that is automatically generated.
    """

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        validate_default=True,
    )

    cls: str = Field(
        default="",
        description=multiline(
            """
            Automatically set to the class's module path and name.
            Do not assign manually.
            """,
        ),
    )

    sid: sid_t = Field(
        default_factory=next_sid,
        description=multiline(
            """
            Auto generated monotonically increasing serial ID.
            Do not assign manually.
            """,
        ),
    )

    @model_validator(mode="before")
    @classmethod
    def validate_auto_fields(cls, data):
        """Set auto-generated fields."""
        if not isinstance(data, dict):
            return data
        data["cls"] = f"{cls.__module__}.{cls.__qualname__}"
        return data

    def __setattr__(self, name: str, value) -> None:
        """Prevent assignment to auto-generated fields after initialization."""
        if name == "cls":
            raise ValueError("Cannot assign to 'cls' field.")
        if name == "sid":
            raise ValueError("Cannot assign to 'sid' field.")
        super().__setattr__(name, value)

    def __str__(self) -> str:
        return prepr(self)
