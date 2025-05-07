from pydantic import Field

from src.core import DataCore
from src.core.util import multiline


class OpenaiLmInitParams(DataCore):

    model_name: str = Field(
        description=multiline(
            """
            Name of the OpenAI model.
            """
        ),
        examples=["gpt-4.1"],
    )
