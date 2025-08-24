from pydantic import Field

from src.core import FuncResult


class LMGentxtResult(FuncResult):
    """Result from language model generation."""

    output_str: str = Field(
        description="Resultant text from model generation.",
    )

    n_input_tokens: int = Field(
        ge=0,
        description="Number of input tokens, as evaluated by the model.",
    )

    n_output_tokens: int = Field(
        ge=0,
        description="Number of output tokens, as evaluated by the model.",
    )
