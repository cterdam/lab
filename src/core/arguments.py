from typing import Literal

from pydantic import Field, RedisDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core import DataCore
from src.core.util import multiline


class Arguments(BaseSettings, DataCore):  # pyright: ignore
    """All args optional."""

    model_config = SettingsConfigDict(
        case_sensitive=True,
        cli_parse_args=True,
        frozen=True,
        validate_default=False,
    )

    # Available arguments begin ###############################################

    task: Literal[
        "dry_run",
        "demo",
    ] = Field(
        default="demo",
        description=multiline(
            """
            Task to perform. All tasks are implemented under src/task.
            """,
        ),
    )

    run_name: str = Field(
        default=None,  # pyright:ignore
        description=multiline(
            """
            Name of the current run which will also used as output dir under
            `out/`. If empty, a unique run name will be generated in its place.
            """
        ),
    )

    REDIS_URL: RedisDsn = Field(
        default="redis://redis:6379/0",  # pyright:ignore
        description=multiline(
            """
            URL for redis server.
            """
        ),
    )

    OPENAI_API_KEY: SecretStr = Field(
        default=None,  # pyright:ignore
        description=multiline(
            """
            Default OpenAI API key.
            """
        ),
    )
