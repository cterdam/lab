"""Update the logger with runtime configs."""

from importlib.resources import files
import os
import sys
from typing import List

from src.config.lab_config import LabConfig
from src.util import multiline

__all__ = [
    "update_logger",
]


def update_logger(logger, config: LabConfig) -> List[str]:
    """Update the logger with runtime configs.

    This func should be called by config scaffold, as a setup step for the configs.

    Args:
        logger (Logger): A loguru logger
        config (LabConfig)

    Returns (List[str]):
        A list of msgs about the logging setup to be logged by its caller. If the stdout
        sink is not configured, also prints them to stdout.
    """

    ###################################################################################
    # Constants

    log_format = "\n".join(
        [
            "<dim>" + "=" * 88,
            "{file.path}:{line} <{function}>",
            "<level>[{level}]</> {time:YYYY-MM-DD HH:mm:ss!UTC}",
            "-" * 88 + "</>",
            "<level>{message}</>",
            "",
        ]
    )

    # Allow all logs
    log_level = 0

    ###################################################################################

    # Collect logging msgs to emit once logger is fully set up
    msgs = []

    # Setup stdout
    if config.log.to_stdout:
        logger.add(sys.stdout, format=log_format, level=log_level)

        msgs.append("Logging to stdout.")
    else:
        msgs.append("NOT logging to stdout.")

    # Setup local log file
    if config.log.to_file:
        file_path = config.general.out_dir / "log.txt"
        logger.add(file_path, format=log_format, level=log_level)

        msgs.append(f"Logging to file at {file_path}")
    else:
        msgs.append("NOT logging to local file.")

    # Set up W&B
    if config.log.to_wandb:

        msgs.append("")
        msgs.append("Setting up wandb.")

        # Must use shell env var to login to W&B
        assert "WANDB_API_KEY" in os.environ
        msgs.append("Wandb API key detected in shell environment.")
        import wandb

        # Use the latest version of W&B backend. See https://wandb.me/wandb-core
        wandb.require("core")

        # Suppress W&B outputs; they are so annoying
        os.environ["WANDB_SILENT"] = "true"
        msgs.append("Wandb direct output suppressed.")

        # Capture console output to W&B logs
        if config.wandb.capture_console:
            os.environ["WANDB_CONSOLE"] = "auto"
            msgs.append("Capturing console output to wandb logs.")
        else:
            os.environ["WANDB_CONSOLE"] = "off"
            msgs.append("NOT capturing console output to wandb logs.")

        # Create W&B run
        wandb.init(
            entity=config.wandb.login_entity,
            project=config.general.project_name,
            name=config.general.run_name,
            id=config.general.run_name,
            dir=config.general.out_dir,
            config=config.to_config_dict(),
            job_type=config.general.task,
            group=config.wandb.run_group,
            tags=config.wandb.run_tags,
            notes=config.wandb.run_notes,
        )

        msgs.append(
            "Logging to wandb at "
            + multiline(
                f"""
                https://wandb.ai
                /{wandb.run.entity}
                /{wandb.run.project}
                /runs
                /{wandb.run.id}
                """,
                is_url=True,
            )
        )

        # Save all source code to W&B
        if config.wandb.save_code:

            asset_name = f"CODE_{config.general.run_name}"

            wandb.run.log_code(
                root=files("src"),
                name=asset_name,
            )

            msgs.append(
                "Source code on wandb at "
                + multiline(
                    f"""
                    https://wandb.ai
                    /{wandb.run.entity}
                    /{wandb.run.project}
                    /artifacts/code
                    /{asset_name}/v0
                    """,
                    is_url=True,
                )
            )
        else:
            msgs.append("NOT saving source code on wandb.")

        msgs.append("Finished setting up wandb.")

    else:
        msgs.append("NOT logging to wandb.")

    # Return logging msgs for caller to log
    if not config.log.to_stdout:
        for msg in msgs:
            print(msg)
    return msgs
