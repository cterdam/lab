"""Logger class."""

from importlib.resources import files
import os
import sys
from typing import Dict, List

from loguru import logger

from src.config.lab_config import LabConfig
from src.util import multiline

__all__ = [
    "LabLogger",
]


class LabLogger:
    """Overall logger class. Can write logs to stdout, local file, and wandb.

    Use the logger just as you would loguru's logger.
        E.g. `logger.info(msg)`.
    """

    def __init__(self):
        """Initialize the logger and prepare for per-config setup."""

        # Use loguru logger as logger
        self._core = logger

        # Remove default stderr handler
        self._core.remove()

        # Make default info level not bold
        self._core.level("INFO", color=logger.level("INFO").color.replace("<bold>", ""))

        # Define common log format for log msgs
        self.log_format = "\n".join(
            [
                "<dim>" + "=" * 88,
                "{file.path}:{line} <{function}>",
                "<level>[{level}]</> {time:YYYY-MM-DD HH:mm:ss!UTC}",
                "-" * 88 + "</>",
                "<level>{message}</>",
                "",
            ]
        )

        # Use in downstream setups to allow all logs
        self.log_level = 0

        # If logging to local file, will be assigned in setup
        self.local_file_path = None

        # If logging to wandb, will be assigned in setup
        self.wandb_run = None

        # If logging to wandb and saving code, will be assigned in setup
        self.wandb_code_artifact = None

    def __getattr__(self, name):
        """Default any method calls not overridden in this class to loguru logger."""
        return getattr(self._core, name)

    def metric(self, metrics: Dict):
        pass

    def setup(self, config: LabConfig) -> List[str]:
        """Update the logger with runtime configs.

        This func should be called by config scaffold, as a setup step for the configs.

        Returns (List[str]):
            A list of msgs about the logging setup to be logged by its caller. If the
            stdout sink is not configured, also prints them to stdout.
        """

        # Collect logging msgs to emit once logger is fully set up
        msgs = []

        # Setup stdout
        if config.log.to_stdout:
            self._core.add(sys.stdout, format=self.log_format, level=self.log_level)

            msgs.append("Logging to stdout.")
        else:
            msgs.append("NOT logging to stdout.")

        # Setup local log file
        if config.log.to_file:
            self.local_file_path = config.general.out_dir / "log.txt"
            self._core.add(
                self.local_file_path, format=self.log_format, level=self.log_level
            )

            msgs.append(f"Logging to file at {self.local_file_path}")
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
            self.wandb_run = wandb.init(
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
                    /{self.wandb_run.entity}
                    /{self.wandb_run.project}
                    /runs
                    /{self.wandb_run.id}
                    """,
                    is_url=True,
                )
            )

            # Code saving
            if config.wandb.save_code:

                artifact_name = f"CODE_{config.general.run_name}"

                self.wandb_code_artifact = self.wandb_run.log_code(
                    root=files("src"),
                    name=artifact_name,
                )

                msgs.append(
                    "Source code on wandb at "
                    + multiline(
                        f"""
                        https://wandb.ai
                        /{wandb.run.entity}
                        /{wandb.run.project}
                        /artifacts/code
                        /{artifact_name}/v0
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
