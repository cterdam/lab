from src.core.log import logger
from src.core.util.constants import PROJECT_ROOT
from src.core.util.general import get_unique_id


def main():

    # Setup starts
    run_id: str = get_unique_id()
    output_dir = PROJECT_ROOT / "out" / run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    log_file_path = output_dir / f"{run_id}.log"
    logger.add_file_sink(log_file_path)
    # Setup complete

    logger.success("Setup complete.")
    logger.info(f"Output in {output_dir.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
