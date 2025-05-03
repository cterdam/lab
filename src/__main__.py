import argparse

from src.core import cfg, ctx, log
from src.core.constants import PROJECT_ROOT
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

    # Make output directory
    ctx.out_dir = PROJECT_ROOT / "out" / run_name
    ctx.out_dir.mkdir(parents=True, exist_ok=True)

    # Make logs
    ctx.log_dir = ctx.out_dir / "log"
    ctx.log_dir.mkdir(parents=True, exist_ok=True)
    log.add_sink(ctx.log_dir / "all.txt")
    log.add_sink(ctx.log_dir / "all.jsonl", serialize=True)

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
