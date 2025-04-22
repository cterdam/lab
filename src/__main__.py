import argparse

from src.core import cfg, ctx, log
from src.core.model.llm import LLM
from src.core.util.constants import PROJECT_ROOT
from src.core.util.data import ppformat
from src.core.util.general import get_type_name, get_unique_id


def parse_args_into_cfg():

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


def setup():
    """Parse args and prepare context."""

    parse_args_into_cfg()

    cfg.run_name = cfg.run_name or get_unique_id()

    ctx.out_dir = PROJECT_ROOT / "out" / cfg.run_name
    ctx.out_dir.mkdir(parents=True, exist_ok=True)
    log.add_file_sink(ctx.out_dir / "log.txt")

    log.success("Setup complete.")
    log.info(ppformat(cfg))


def main():
    setup()

    llm = LLM("deepseek/deepseek-chat")
    result = llm.generate("Hi!")
    log.info(f"Test LLM generate: {result}")


if __name__ == "__main__":
    main()
