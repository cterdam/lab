import sys

from src.core import Logger
from src.core.arguments import Arguments
from src.core.environment import Environment
from src.core.util import REPO_ROOT, prepr


def set_root_logger() -> Logger:
    """Prepare src logger."""

    # Remove default sink
    Logger.remove_sink(0)

    # Configure global sinks
    base = Logger._base_logger()
    base.add(sys.stderr, level=10, format=Logger._LOG_FORMAT, enqueue=True)
    base.add(
        env.log_dir / "all.txt",
        level=Logger._LOG_LEVEL,
        format=Logger._LOG_FORMAT,
        colorize=True,
        enqueue=True,
    )

    return Logger(logname=env.ROOT_LOGNAME)


def setup_msg() -> None:
    """Emit setup msgs as logs."""
    log.success(prepr(arg))
    if not arg.run_name:
        log.warning(f"Run name randomly initialized to {env.run_name}")


arg: Arguments = Arguments(_env_file=[REPO_ROOT / "args"])  # type: ignore
env: Environment = Environment()
log: Logger = set_root_logger()

setup_msg()
