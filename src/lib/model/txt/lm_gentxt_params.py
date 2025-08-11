from pydantic import Field

from src.core import Dataclass
from src.core.util import multiline


class LMGentxtParams(Dataclass):
    """Parameters for language model generation."""

    system_prompt: str | None = Field(
        default=None,
        description=multiline(
            """
            System prompt for generation. For models not supporting an explicit
            field to hold the system prompt, this will be concatenated into the
            prompt as a prefix.
            """
        ),
    )

    prompt: str = Field(
        description=multiline(
            """
            User prompt for generation, excluding the system prompt.
            """
        )
    )

    max_new_tokens: int | None = Field(
        default=None,
        ge=0,
        description=multiline(
            """
            Max number of tokens to allow the model to generate, not counting
            tokens in the prompt.
            """
        ),
    )

    temperature: float = Field(
        default=1.0,
        description=multiline(
            """
            When positive, lower is more deterministic, higher is more random.
            """
        ),
    )

    top_p: float = Field(
        default=1.0,
        ge=0,
        le=1,
        description=multiline(
            """
            Lower is more deterministic, higher is more random.
            """
        ),
    )
