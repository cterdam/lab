from typing import Literal

from pydantic import Field, RedisDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core import Dataclass
from src.core.util import multiline


class Arguments(BaseSettings, Dataclass):  # type: ignore
    """All args optional."""

    model_config = SettingsConfigDict(
        case_sensitive=True,
        cli_parse_args=True,
        frozen=True,
        validate_default=True,
    )

    # Available arguments begin ###############################################

    task: Literal[
        "dry_run",
        "demo",
    ] = Field(
        default="demo",
        description=multiline(
            """
            The task to perform. All tasks are implemented under src/task.
            """,
        ),
    )

    run_name: str | None = Field(
        default=None,
        min_length=1,
        description=multiline(
            """
            Name of the current run which will also used as output dir under
            `out/`. If empty, a unique run name will be generated in its place.
            """
        ),
    )

    REDIS_URL: RedisDsn = Field(
        default=RedisDsn("redis://redis:6379/0"),
        description="URL for redis server.",
    )

    OPENAI_API_KEY: SecretStr | None = Field(
        default=None,
        description="Default OpenAI API key.",
    )
