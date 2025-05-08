import os
import typing
from functools import cache, partial
from pathlib import Path

import loguru

from src.core.util import multiline


class Logger:
    """Overall base class for anything that keeps its own log file.

    Descendants inherit self.log, a Loguru logger bound to a unique logger_id.
    This can be used to write logs to stdout and has its own file sink.
        E.g. `player.log.info(msg)`
    """

    # Each descendant class can add a layer in its log dir path by overriding
    namespace_part: str = "log"

    # Allow all logs for downstream sinks
    log_level = 0

    # Default log format
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

    def __init__(self, *args, log_name: str, **kwargs):
        """Initialize this instance’s logger.

        Args:
            log_name (str): Unique name for this instance’s log files.
        """

        # Lazy import to avoid circular import problem
        from src import env

        # Build up namespace from class hierarchy
        _namespace = [
            part
            for cls in reversed(self.__class__.__mro__)
            if (part := cls.__dict__.get("namespace_part"))
        ]

        # Bind unique ID for this logger
        self._logger_id = f"{'.'.join(_namespace)}:{log_name}"
        if self._logger_id in env.loggers:
            raise ValueError(f"Duplicate logger ID: {self._logger_id}")
        env.loggers[self._logger_id] = self
        self.log = Logger._base_logger().bind(logger_id=self._logger_id)

        # Add file sinks
        _namespace_dir = env.out_dir.joinpath(*_namespace)
        only_self = partial(Logger._only_id, logger_id=self._logger_id)
        Logger.add_sink(
            _namespace_dir / f"{log_name}.txt",
            log_filter=only_self,
        )
        Logger.add_sink(
            _namespace_dir / f"{log_name}.jsonl",
            log_filter=only_self,
            serialize=True,
        )

        super().__init__(*args, **kwargs)

    def __getattr__(self, name):
        """Default any attrs not overridden in this class to loguru logger."""
        return getattr(self.log, name)

    @staticmethod
    @cache
    def _base_logger():
        """All derivative loggers from this class should base on this logger."""
        from src import env

        # Use loguru logger with relative path
        logger = loguru.logger.patch(
            lambda record: record["extra"].update(
                relpath=os.path.relpath(record["file"].path, env.repo_root)
            )
        )
        return logger

    @classmethod
    def add_sink(
        cls,
        sink: Path | typing.TextIO,
        level: int | None = None,
        log_format: str | None = None,
        log_filter: typing.Callable | None = None,
        serialize=False,
    ) -> int:
        """Attach a sink to the underlying shared Loguru logger.

        Returns:
            An integer sink ID, which can later be used to remove the sink.
        """
        return cls._base_logger().add(
            sink=sink,
            level=level or cls.log_level,
            format=log_format or cls.log_format,
            filter=log_filter,
            serialize=serialize,
        )

    @classmethod
    def remove_sink(cls, sink_id: int) -> None:
        """Remove a previously added sink from the shared logger.

        Args:
            sink_id (int): The integer handle returned by `add_sink`.
        """
        cls._base_logger().remove(sink_id)

    @staticmethod
    def _only_id(record, logger_id):
        """Loguru filter: only allow records matching the given logger_id."""
        return record["extra"]["logger_id"] == logger_id
