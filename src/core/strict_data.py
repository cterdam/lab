from pprint import pformat

from pydantic import BaseModel, ConfigDict


class StrictData(BaseModel):
    """Dataclass with strict guarantees."""

    model_config = ConfigDict(
        validate_default=True,
        validate_assignment=True,
        extra="forbid",
    )

    def format_str(self) -> str:
        """Format contents as pretty string."""
        return pformat(self.model_dump())
