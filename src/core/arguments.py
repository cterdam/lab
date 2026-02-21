from typing import Literal

from pydantic import Field, RedisDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core.util import multiline


class Arguments(BaseSettings):
    """All args optional."""

    model_config = SettingsConfigDict(
        case_sensitive=True,
        cli_parse_args=True,
        extra="ignore",
        frozen=True,
        validate_default=True,
    )

    # Available arguments begin ###############################################

    task: Literal[
        "dry_run",
        "demo",
        "algo",
    ] = Field(
        default="demo",
        description=multiline(
            """
            The task to perform. All tasks are implemented under src/task.
            """,
        ),
    )

    algo: str = Field(
        default="src.lib.algo.aswan.AswanNormal",
        description=multiline(
            """
            Import path of the algo to launch (for task=algo),
            e.g. src.lib.algo.aswan.AswanNormal.
            """,
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

    # Algo params ##############################################################

    M: int = Field(default=0)
    N: int = Field(default=0)
    Ns: int = Field(default=0)
    p: float = Field(default=0)
    y: float = Field(default=0)
