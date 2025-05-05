import os
import pathlib
import typing

import loguru

from src.core.constants import PROJECT_ROOT
from src.core.util import multiline


class Logger:
    """Overall base class for anything that keeps its own log file.

    Can write logs to stdout, local file, and more via the `log` attribute.
        E.g. `player.log.info(msg)`.
    """

    # Since this base class is the highest in MRO, this will be the log dir name
    # Each descendant class can create a dir layer by setting this str
    namespace_part: str = "log"

    # Reject duplicate logger IDs
    registered_logger_ids = set()

    # Use loguru logger with relative path
    _logger = loguru.logger.patch(
        lambda record: record["extra"].update(
            relpath=os.path.relpath(record["file"].path, PROJECT_ROOT)
        )
    )

    # Allow all logs for downstream sinks
    log_level = 0

    # Define common log format for log msgs
    log_format = "\n".join(
        [
            "<dim>" + "─" * 88,
            multiline(
                """
                </><level>[{level:.4}]</><dim> {time:YYYY-MM-DD HH:mm:ss!UTC}
                <{extra[logger_id]}> {extra[relpath]}:{line} </>
                """
            ),
            "{message}",
        ]
    )

    def __init__(self, log_name: str, *args, **kwargs):
        """Initialize the logger.

        Args:
            log_name (str): name of the file holding all logs from self.
        """

        # Lazy import to avoid circular import problem
        from src import ctx

        # Build up namespace from class hierarchy
        _namespace = [
            part
            for cls in reversed(self.__class__.__mro__)
            if (part := cls.__dict__.get("namespace_part"))
        ]

        # Make dir to hold self log
        _namespace_dir = ctx.out_dir.joinpath(*_namespace)
        _namespace_dir.mkdir(parents=True, exist_ok=True)

        # Bind unique ID for this logger
        self._logger_id = f"{'.'.join(_namespace)}:{log_name}"
        if self._logger_id in self.registered_logger_ids:
            raise ValueError(f"Duplicate logger ID: {self._logger_id}")
        self.registered_logger_ids.add(self._logger_id)
        self.log = self._logger.bind(logger_id=self._logger_id)

        # Add file sinks
        self.add_sink(
            _namespace_dir / f"{log_name}.txt",
            log_filter=lambda record: record["extra"]["logger_id"] == self._logger_id,
        )
        self.add_sink(
            _namespace_dir / f"{log_name}.jsonl",
            log_filter=lambda record: record["extra"]["logger_id"] == self._logger_id,
            serialize=True,
        )

        super().__init__(*args, **kwargs)

    def __getattr__(self, name):
        """default any attrs not overridden in this class to loguru logger."""
        return getattr(self.log, name)

    def add_sink(
        self,
        sink: pathlib.Path | typing.TextIO,
        level: int | None = None,
        log_format: str | None = None,
        log_filter: typing.Callable | None = None,
        serialize=False,
    ) -> int:
        return self.log.add(
            sink=sink,
            level=level or self.log_level,
            format=log_format or self.log_format,
            filter=log_filter,
            serialize=serialize,
        )
