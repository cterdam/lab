from pprint import pformat

from pydantic import BaseModel, ConfigDict


class Config(BaseModel):
    """Base dataclass with strict guarantees."""

    model_config = ConfigDict(
        validate_default=False,
        validate_assignment=True,
        extra="forbid",
    )

    def format_str(self) -> str:
        """Format contents as pretty string."""
        return pformat(self.model_dump())
