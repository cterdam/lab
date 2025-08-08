from pydantic import Field

from src.core import Dataclass
from src.core.util import multiline


class LmCoke(Dataclass):
    """COunter KEys related to language models."""

    INPUT_TOKEN: str = Field(
        default="input_tokens",
        min_length=1,
        description=multiline(
            """
            Counter key to tally all input tokens for language models.
            """
        ),
    )

    OUTPUT_TOKEN: str = Field(
        default="output_tokens",
        min_length=1,
        description=multiline(
            """
            Counter key to tally all output tokens from language models.
            """
        ),
    )

    GENTXT_INVOC: str = Field(
        default="gentxt_invoc",
        min_length=1,
        description=multiline(
            """
            Counter key to tally invocations of language model text gen.
            """
        ),
    )

    AGENTXT_INVOC: str = Field(
        default="agentxt_invoc",
        min_length=1,
        description=multiline(
            """
            Counter key to tally invocations of language model async text gen.
            """
        ),
    )
