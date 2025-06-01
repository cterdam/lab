import argparse
import asyncio
import sys
import typing

from src.core import Logger
from src.core.arguments import Arguments
from src.core.environment import Environment
from src.core.util import multiline


def parse_args() -> Arguments:
    """Parse and return user-supplied args.

    Do not log inside this func as the logger is not configured yet.
    """

    def get_type_name(t) -> str:
        """Given a type, infer the class name in str.

        Examples:
        >>> get_type_name(int)
        'int'
        >>> get_type_name(Literal["red", "green"])
        'Literal[red, green]'
        """
        if typing.get_origin(t) is typing.Literal:
            # Literal type
            return "Literal[" + ", ".join(str(arg) for arg in typing.get_args(t)) + "]"
        elif hasattr(t, "__name__"):
            # Primitive type
            return t.__name__
        else:
            return str(t)

    # Define parser
    parser = argparse.ArgumentParser(
        prog="PROG",
        usage="%(prog)s (--<opt_name> <opt_value>)*",
        description=("All opt values optional."),
    )

    # Parse args
    for field_name, field_info in Arguments.model_fields.items():
        parser.add_argument(
            f"--{field_name}",
            metavar=f"[{get_type_name(field_info.annotation)}]",
            required=False,
            type=str,
            help=field_info.description,
        )

    # Store into config
    supplied_args = {
        arg_name: arg_val
        for arg_name, arg_val in vars(parser.parse_args()).items()
        if arg_val
    }
    return Arguments(**supplied_args)


def set_logger() -> Logger:
    """Prepare src logger."""

    # Remove default stderr sink
    Logger.remove_sink(0)

    # Configure sinks
    Logger.add_sink(sys.stdout, level=10)
    Logger.add_sink(env.log_dir / "all.txt")
    Logger.add_sink(env.log_dir / "all.jsonl", serialize=True)

    return Logger(log_name="root")


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
        log.warning("Run name is randomly initialized.")

    log.info(f"Output in {env.out_dir}")


arg: Arguments = parse_args()
env: Environment = Environment()
log: Logger = set_logger()

setup_msg()
