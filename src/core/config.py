import textwrap
from pprint import pformat

from pydantic import BaseModel, ConfigDict


class Config(BaseModel):
    """Base dataclass with strict guarantees."""

    model_config = ConfigDict(
        validate_default=True,
        validate_assignment=True,
        extra="forbid",
    )

    def format_str(self, indent=0) -> str:
        """Format contents as pretty string.

        Args:
            indent (int): Number of whitespace to indent on all lines.
        """
        return textwrap.indent(pformat(self.model_dump()), " " * indent)
