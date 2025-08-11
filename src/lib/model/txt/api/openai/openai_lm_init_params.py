from pydantic import Field, SecretStr

from src import arg
from src.core import Dataclass
from src.core.util import multiline


class OpenAILMInitParams(Dataclass):

    model_name: str = Field(
        description=multiline(
            """
            Name of the OpenAI model.
            """
        ),
        examples=["gpt-4.1"],
    )

    api_key: SecretStr = Field(
        default=arg.OPENAI_API_KEY,
        description=multiline(
            """
            API key to use for this model.
            """
        ),
    )
