from pydantic import Field

from src.core import Dataclass
from src.core.util import multiline


class LMGentxtResult(Dataclass):
    """Result from language model generation."""

    output: str = Field(
        description=multiline(
            """
            Resultant text from model generation.
            """
        ),
    )

    input_tokens: int = Field(
        ge=0,
        description=multiline(
            """
            Number of input tokens, as evaluated by the model.
            """
        ),
    )

    output_tokens: int = Field(
        ge=0,
        description=multiline(
            """
            Number of output tokens, as evaluated by the model.
            """
        ),
    )
