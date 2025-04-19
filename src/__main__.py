import pathlib

from src.log import logger
from src.util.constants import PROJECT_ROOT
from src.util.general import get_unique_id


def main():

    # Setup starts
    run_id: str = get_unique_id()
    output_dir: pathlib.Path = PROJECT_ROOT / "out" / run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    log_file_path: pathlib.Path = output_dir / f"{run_id}.log"
    logger.add_file_sink(log_file_path)
    # Setup complete

    logger.info("Setup complete.")
    logger.info(f"Output in {output_dir}")


if __name__ == "__main__":
    main()
