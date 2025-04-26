import os
import pathlib
import sys

from loguru import logger

from src.core.constants import PROJECT_ROOT
from src.core.util import multiline


class Logger:
    """Overall logger class. Can write logs to stdout, local file, and more.

    Use the logger in the same way as loguru's logger.
        E.g. `logger.info(msg)`.
    """

    def __init__(self):

        # Use loguru logger as internal logger
        self._core = logger

        # Use relative file path in logs
        self._core = self._core.patch(
            lambda record: record["extra"].update(
                relpath=os.path.relpath(record["file"].path, PROJECT_ROOT)
            )
        )

        # Define common log format for log msgs
        self._msg_format = "\n".join(
            [
                "<dim>" + "─" * 88,
                multiline(
                    """
                    </><level>[{level}]</><dim> {time:YYYY-MM-DD HH:mm:ss!UTC}
                    {extra[relpath]}:{line}</>
                    """
                ),
                "{message}",
            ]
        )

        # Allow all logs for downstream sinks
        self._log_level = 0

        # Remove default stderr sink
        self._core.remove()

        # Add stdout sink
        self._core.add(
            sys.stdout,
            format=self._msg_format,
            level=self._log_level,
        )

    def __getattr__(self, name):
        """Default any attrs not overridden in this class to loguru logger."""
        return getattr(self._core, name)

    def add_file_sink(self, filepath: pathlib.Path):
        self._core.add(filepath, format=self._msg_format, level=self._log_level)
