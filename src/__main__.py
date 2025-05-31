import argparse
import importlib
import sys

from src import arg, env
from src.core import Logger
from src.core.util import get_type_name, multiline


def parse_args():
    """Parse and store args into cfg.

    Do not log inside this func as the logger is not configured yet.
    """

    # Define parser
    parser = argparse.ArgumentParser(
        prog="PROG",
        usage="%(prog)s (--<opt_name> <opt_value>)*",
        description=("All opt values optional."),
    )

    # Parse args
    for field_name, field_info in arg.model_fields.items():
        parser.add_argument(
            f"--{field_name}",
            metavar=f"[{get_type_name(field_info.annotation)}]",
            required=False,
            type=str,
            help=field_info.description,
        )

    # Store into config
    for arg_name, arg_val in vars(parser.parse_args()).items():
        if arg_val is not None:
            setattr(arg, arg_name, arg_val)


def set_logger():
    """Prepare runtime context."""

    # Configure default sinks
    Logger.remove_sink(0)
    Logger.add_sink(sys.stdout)
    Logger.add_sink(env.log_dir / "all.txt")
    Logger.add_sink(env.log_dir / "all.jsonl", serialize=True)

    # Inject root logger to src
    log = Logger(log_name="root")
    importlib.import_module("src").log = log  # pyright:ignore

    # Setup complete, logger ready
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
    log.info(f"Output in {env.out_dir}")


def run_task():
    match arg.task:
        case "dry_run":
            from src.task.dry_run import main

            main()

        case "demo":
            from src.task.demo import main

            main()

        case "content_generation":
            from src.task.content_generation import main

            main()


def main():
    parse_args()
    set_logger()
    run_task()


if __name__ == "__main__":
    main()
