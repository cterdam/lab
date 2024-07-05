"""Various pre-processing steps for config options after parsing."""

from importlib.resources import files

from src.log import logger
from src.util import get_random_state_setter, get_unique_id

from .lab_config import LabConfig

__all__ = [
    "scaffold",
]


def scaffold(config: LabConfig):
    """Process config options that require setup."""

    # Collect logging msgs to emit once logger is set up
    msgs = ["Beginning run.", ""]

    # Set up run name
    if config.general.run_identifier:
        config.general.run_name += "-" + get_unique_id()
        msgs.append("Unique identifier appended to run name.")
    else:
        msgs.append("NOT appending unique identifier to run name.")
    msgs.append(f"Run name set to {repr(config.general.run_name)}")

    # Set up out dir
    if config.general.out_dir is None:
        config.general.out_dir = (
            files("src")
            / ".."
            / "out"
            / config.general.project_name
            / config.general.run_name
        )
    config.general.out_dir = config.general.out_dir.resolve()
    msgs.append(f"Out dir set to {config.general.out_dir}")

    # ONLY STEPS CONCERNING LOGGER ABOVE THIS LINE ------------------------------------

    # Set up logger
    msgs.append("")
    logger_setup_msgs = logger.setup(config)
    msgs.extend(logger_setup_msgs)

    # Logger is set up, emit all msgs so far
    logger.trace("\n".join(msgs))

    # ANY OTHER STEP & CAN USE LOGGER BELOW THIS LINE ---------------------------------

    # Snapshot environment
    #   - python ver, libraries ver, git hash and any uncommitted edits, username, host
    #     , torch devices
    #   - ram, disk space

    # Set up random state
    get_random_state_setter(config, logger)()

    # Log setup msgs and resultant configs
    logger.info("Finished setting up all configs.\n" + str(config))
