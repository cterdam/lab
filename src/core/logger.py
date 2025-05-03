import os
import pathlib
import sys
import typing

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
        self._log_format = "\n".join(
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
        self.add_sink(sys.stdout)

    def __getattr__(self, name):
        """Default any attrs not overridden in this class to loguru logger."""
        return getattr(self._core, name)

    def add_sink(
        self,
        sink: pathlib.Path | typing.TextIO,
        level: int | None = None,
        log_format: str | None = None,
        log_filter: typing.Callable | None = None,
        serialize=False,
    ):
        if level is None:
            level = self._log_level
        if log_format is None:
            log_format = self._log_format
        self._core.add(
            sink=sink,
            level=level,
            format=log_format,
            filter=log_filter,
            serialize=serialize,
        )
