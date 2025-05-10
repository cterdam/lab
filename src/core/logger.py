from __future__ import annotations

import functools
import inspect
import os
import pathlib
import textwrap
import typing

import loguru

from src.core.util import multiline


class Logger:
    """Overall base class for anything that keeps its own log file.

    Descendants inherit self.log, a logger bound to a unique logger_id. This
    can be used to write logs to stdout and keeps its own file sink.
        E.g. `player.log.info(msg)`

    This class also provides decorators, input(), output(), and io(), for
    logging a function's input and output.
    """

    # Each descendant class can add a layer in its log dir path by overriding
    namespace_part: str = "log"

    # Allow all logs for downstream sinks
    _log_level = 0

    # Default log format
    _log_format = "\n".join(
        [
            "<level>[{level:^8}] " + "─" * 49 + "</> {time:YYYY-MM-DD HH:mm:ss!UTC}",
            # "<dim><{extra[logger_id]}> {extra[relpath]}:{line}</>",
            "<dim>{extra[header]}</>",
            "{message}",
        ]
    )

    # Params for configuring severity colorschemes
    _func_input_severity_name = "-> FINP"
    _func_output_severity_name = "FOUT ->"
    _counter_severity_name = "COUNT"
    _custom_severity_names = [
        _func_input_severity_name,
        _func_output_severity_name,
        _counter_severity_name,
    ]
    _severities = [
        ("TRACE", 5, "#505050"),
        (_func_input_severity_name, 7, "#38758A"),
        (_func_output_severity_name, 8, "#4A6FA5"),
        ("DEBUG", 10, "#C080D3"),
        (_counter_severity_name, 15, "#DAA520"),
        ("INFO", 20, "#5FAFAC"),
        ("SUCCESS", 25, "#2E8B57"),
        ("WARNING", 30, "#E09C34"),
        ("ERROR", 40, "#E04E3A"),
        ("CRITICAL", 50, "#FF0000"),
    ]

    # Msg format for specific msg types
    _func_input_msg = multiline(
        """
        -> {class_name}.{func_name}(...)
        {func_args}
        """,
        oneline=False,
    )
    _func_output_msg = multiline(
        """
        {class_name}.{func_name}(...) ->
        {func_result}
        """,
        oneline=False,
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
        self.log = self._base_logger().bind(logger_id=self._logger_id)

        # Add file sinks
        _namespace_dir = env.out_dir.joinpath(*_namespace)
        only_self = functools.partial(self._filter_by_id, logger_id=self._logger_id)
        self.add_sink(
            _namespace_dir / f"{log_name}.txt",
            log_filter=only_self,
        )
        self.add_sink(
            _namespace_dir / f"{log_name}.jsonl",
            log_filter=only_self,
            serialize=True,
        )

        super().__init__(*args, **kwargs)

    def __getattr__(self, name):
        """Default any attrs not overridden in this class to loguru logger."""
        return getattr(self.log, name)

    @staticmethod
    @functools.cache
    def _base_logger():
        """Use class-level attributes to register the base logger.

        This function code will only run once as there is only one base logger
        in the loguru methodology. Subsequent calls will hit the functools.cache
        instead.

        All derivative loggers from this class should base on this logger."""

        # Use loguru logger
        logger = loguru.logger

        # Send relative path and header str with records
        logger = logger.patch(Logger._patch_relpath)
        logger = logger.patch(Logger._patch_header)

        # Configure logging severities with colorscheme
        for name, no, fg in Logger._severities:
            if name in Logger._custom_severity_names:
                # Custom severity, register here
                logger.level(
                    name=name,
                    no=no,
                    color=f"<bold><fg {fg}>",
                    icon="",
                )
            else:
                # Build-in severity, just change color and icon here
                logger.level(
                    name=name,
                    color=f"<bold><fg {fg}>",
                    icon="",
                )

        return logger

    @classmethod
    def add_sink(
        cls,
        sink: pathlib.Path | typing.TextIO,
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
            level=level or cls._log_level,
            format=log_format or cls._log_format,
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
    def _filter_by_id(record: loguru.Record, logger_id: str):
        """Loguru filter to only allow records matching the given logger_id"""
        return record["extra"]["logger_id"] == logger_id

    @staticmethod
    def _patch_relpath(record: loguru.Record) -> None:
        """Loguru patch to add an extra field for relative path."""
        from src import env

        record["extra"]["relpath"] = os.path.relpath(record["file"].path, env.repo_root)

    @staticmethod
    def _patch_header(record: loguru.Record) -> None:
        """Loguru patch to add a header str as extra field."""
        from src import env

        # "<dim><{extra[logger_id]}> {extra[relpath]}:{line}</>",
        left = record["extra"]["logger_id"]
        right = record["extra"]["relpath"] + ":" + str(record["line"])
        separator = " | "
        n_spaces = env.max_linelen - len(left) - len(right)
        if n_spaces < len(separator):
            header = left + separator + right
        else:
            header = left + " " * n_spaces + right
        record["extra"]["header"] = header

    @classmethod
    def input(cls, depth: int = 1):
        """
        Decorator to log the inputs passed into a function.

        The function to decorate needs to be a method of an instance of a
        descendant of this class. Logs will be emitted using the instance's own
        logger.

        Normally, the input logs will be emitted before function execution. An
        exception is when this decorator is used on the __init__ function, in
        which case input logging has to be delayed until function return. The
        reason is the instance's logger does not exist prior to that point.

        Args:
            depth: The number of stack frames to skip when attributing the log.
            Useful when it's nested inside other decorators.
        """
        from src import env

        def decorator(func):

            is_init = func.__name__ == "__init__"

            @functools.wraps(func)
            def wrapped_func(*args, **kwargs):
                self = args[0]
                bound_args = inspect.signature(func).bind_partial(*args, **kwargs)
                bound_args.apply_defaults()
                func_args = {
                    k: v for k, v in bound_args.arguments.items() if k != "self"
                }
                if not is_init:
                    self.log.opt(depth=depth).log(
                        cls._func_input_severity_name,
                        cls._func_input_msg,
                        class_name=self.__class__.__name__,
                        func_name=func.__name__,
                        func_args=env.repr(func_args),
                    )
                func_result = func(*args, **kwargs)
                if is_init:
                    self.log.opt(depth=depth).log(
                        cls._func_input_severity_name,
                        cls._func_input_msg,
                        class_name=self.__class__.__name__,
                        func_name=func.__name__,
                        func_args=env.repr(func_args),
                    )
                return func_result

            return wrapped_func

        return decorator

    @classmethod
    def output(cls, depth: int = 1):
        """
        Decorator to log the outputs returned from a function.

        The function to decorate needs to be a method of an instance of a
        descendant of this class. Logs will be emitted using the instance's own
        logger.

        Args:
            depth: The number of stack frames to skip when attributing the log.
            Useful when it's nested inside other decorators.
        """
        from src import env

        def decorator(func):
            @functools.wraps(func)
            def wrapped_func(*args, **kwargs):
                self = args[0]
                func_result = func(*args, **kwargs)
                self.log.opt(depth=depth).log(
                    cls._func_output_severity_name,
                    cls._func_output_msg,
                    class_name=self.__class__.__name__,
                    func_name=func.__name__,
                    func_result=textwrap.indent(
                        env.repr(
                            func_result,
                            max_width=env.max_linelen - env.indent,
                            indent=env.indent,
                        ),
                        prefix=" " * env.indent,
                    ),
                )
                return func_result

            return wrapped_func

        return decorator

    @classmethod
    def io(cls, depth: int = 1):
        """
        Return a decorator that logs both method inputs and outputs.

        The function to decorate needs to be a method of an instance of a
        descendant of this class. Logs will be emitted using the instance's own
        logger.

        Normally, the input logs will be emitted before function execution. An
        exception is when this decorator is used on the __init__ function, in
        which case input logging has to be delayed until function return. The
        reason is the instance's logger does not exist prior to that point.

        Args:
            depth: The number of stack frames to skip when attributing the log.
            Useful when it's nested inside other decorators.
        """

        def decorator(func):
            return cls.output(depth)(cls.input(depth + 1)(func))

        return decorator
