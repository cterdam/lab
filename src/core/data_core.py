import textwrap
from pprint import pformat

from pydantic import BaseModel, ConfigDict


class DataCore(BaseModel):
    """Base dataclass with strict guarantees and handy properties."""

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
        return textwrap.indent(
            pformat(self.model_dump(), width=80 - indent), " " * indent
        )
