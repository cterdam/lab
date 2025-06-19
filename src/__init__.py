import sys

from src.core import Logger
from src.core.arguments import Arguments
from src.core.environment import Environment
from src.core.util import multiline


def set_logger() -> Logger:
    """Prepare src logger."""

    # Remove default stderr sink
    Logger.remove_sink(0)

    # Configure sinks
    Logger.add_sink(sys.stdout, level=10)
    Logger.add_sink(env.log_dir / "all.txt")
    Logger.add_sink(env.log_dir / "all.colo.txt", colorize=True)
    Logger.add_sink(env.log_dir / "all.jsonl", serialize=True)

    return Logger(logname="root")


def setup_msg() -> None:
    """Emit setup msgs as logs."""

    log.success(
        multiline(
            """
            Finished setup with args:
            {arg}
            """,
            oneline=False,
        ),
        arg=arg,
    )

    if not arg.run_name:
        log.warning(f"Run name is randomly initialized to {env.run_name}")


env: Environment = Environment()
arg: Arguments = Arguments(_env_file=env.repo_root / ".env")  # pyright:ignore
log: Logger = set_logger()

setup_msg()
