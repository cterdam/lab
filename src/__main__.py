import argparse
import importlib
import sys

from src import cfg, ctx
from src.core.constants import PROJECT_ROOT
from src.core.logger import Logger
from src.core.util import get_type_name, get_unique_id


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
    for field_name, field_info in cfg.model_fields.items():
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
            setattr(cfg, arg_name, arg_val)


def prepare_runtime():
    """Prepare runtime context."""

    # Determine run name
    run_name = cfg.run_name or get_unique_id()

    # Make out dir
    ctx.out_dir = PROJECT_ROOT / "out" / run_name
    ctx.out_dir.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    log = Logger(log_name="root")
    log.remove(0)
    log.add_sink(sys.stdout)
    log.add_sink(ctx.out_dir / Logger.namespace_part / "all.txt")
    log.add_sink(ctx.out_dir / Logger.namespace_part / "all.jsonl", serialize=True)

    # Inject logger to src
    importlib.import_module("src").log = log  # pyright:ignore

    # Setup complete, logger ready
    log.success("Setup complete. Config opts:\n" + cfg.format_str())
    log.info(f"Output in {ctx.out_dir}")


def run_task():
    match cfg.task:
        case "dry_run":
            from src.task.dry_run import main

            main()


def main():
    parse_args()
    prepare_runtime()
    run_task()


if __name__ == "__main__":
    main()
