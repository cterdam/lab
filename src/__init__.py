import sys

from beartype.claw import beartype_this_package

from src.core import Logger
from src.core.arguments import Arguments
from src.core.environment import Environment
from src.core.util import REPO_ROOT, prepr

beartype_this_package()


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


arg: Arguments = Arguments(_env_file=[REPO_ROOT / "args"])  # type: ignore
env: Environment = Environment()
log: Logger = set_root_logger()

log.success(prepr(arg))
log.success(f"Run ID: {env.run_id}")
log.success(f"RedisInsight: {env.redis_insight}")
