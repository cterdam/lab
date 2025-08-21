from pydantic import Field, SecretStr

from src import arg
from src.core import Dataclass


class OpenAILMInitParams(Dataclass):

    model_name: str = Field(
        description="Name of the OpenAI model.",
        examples=["gpt-4.1"],
    )

    api_key: SecretStr = Field(
        default=arg.OPENAI_API_KEY,
        description="API key to use for this model.",
    )
