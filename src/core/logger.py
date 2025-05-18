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
    namespace_part: str | None = None

    # Allow all logs for downstream sinks
    _LOG_LEVEL = 0

    # Default log format
    _LOG_FORMAT = (
        multiline(
            """
            <green>{time:YYYY-MM-DD HH:mm:ss!UTC}</> <level>[{level:^8}]</>
            <dim><cyan>{extra[logger_id]}</></> | <dim><yellow>{extra[relpath]}:{line}</></>
            """
        )
        + "\n{message}"
    )

    # Params for configuring levels and colorschemes
    _FUNC_INPUT_LEVEL_NAME = "-> FINP"
    _FUNC_OUTPUT_LEVEL_NAME = "FOUT ->"
    _COUNTER_LEVEL_NAME = "COUNT"
    _CUSTOM_LEVEL_NAMES = [
        _FUNC_INPUT_LEVEL_NAME,
        _FUNC_OUTPUT_LEVEL_NAME,
        _COUNTER_LEVEL_NAME,
    ]
    _LEVELS = [
        ("TRACE", 5, "#505050"),
        (_FUNC_INPUT_LEVEL_NAME, 7, "#38758A"),
        (_FUNC_OUTPUT_LEVEL_NAME, 8, "#4A6FA5"),
        ("DEBUG", 10, "#C080D3"),
        (_COUNTER_LEVEL_NAME, 15, "#DAA520"),
        ("INFO", 20, "#5FAFAC"),
        ("SUCCESS", 25, "#2E8B57"),
        ("WARNING", 30, "#E09C34"),
        ("ERROR", 40, "#E04E3A"),
        ("CRITICAL", 50, "#FF0000"),
    ]

    # Msg format for specific msg types
    _FUNC_INPUT_MSG = multiline(
        """
        -> {class_name}.{func_name}(...)
        {func_args}
        """,
        oneline=False,
    )
    _FUNC_OUTPUT_MSG = multiline(
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
        self._logger_id = (
            f"{'.'.join(_namespace)}:{log_name}" if _namespace else log_name
        )
        if self._logger_id in env.loggers:
            raise ValueError(f"Duplicate logger ID: {self._logger_id}")
        env.loggers[self._logger_id] = self
        self.log = Logger._base_logger().bind(logger_id=self._logger_id)

        # Add file sinks
        _namespace_dir = env.log_dir.joinpath(*_namespace)
        only_self = lambda record: record["extra"]["logger_id"] == self._logger_id
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
    @functools.cache
    def _base_logger():
        """Use class-level attributes to register the base logger.

        This function code will only run once as there is only one base logger
        in the loguru methodology. Subsequent calls will hit the functools.cache
        instead.

        All derivative loggers from this class should base on this logger."""

        from src import env

        # Use loguru logger
        logger = loguru.logger

        # Send relative path and header str with records
        logger = logger.patch(
            lambda record: record["extra"].update(
                relpath=os.path.relpath(record["file"].path, env.repo_root)
            )
        )

        # Configure logging levels with colorscheme
        for name, no, fg in Logger._LEVELS:
            if name in Logger._CUSTOM_LEVEL_NAMES:
                # Custom level, register here
                logger.level(
                    name=name,
                    no=no,
                    color=f"<bold><fg {fg}>",
                    icon="",
                )
            else:
                # Builtin level, just change color and icon here
                logger.level(
                    name=name,
                    color=f"<bold><fg {fg}>",
                    icon="",
                )

        return logger

    @staticmethod
    def add_sink(
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
        return Logger._base_logger().add(
            sink=sink,
            level=level or Logger._LOG_LEVEL,
            format=log_format or Logger._LOG_FORMAT,
            filter=log_filter,
            serialize=serialize,
        )

    @staticmethod
    def remove_sink(sink_id: int) -> None:
        """Remove a previously added sink from the shared logger.

        Args:
            sink_id (int): The integer handle returned by `add_sink`.
        """
        Logger._base_logger().remove(sink_id)

    @staticmethod
    def _get_async_pad() -> int:
        """Helper for func input output decorators to find depth pad number.

        Inspect the current call stack and, beyond the decorator wrapper itself,
        skip over any asyncio internals so that logs attribute correctly to the
        user’s call site for a coroutine.
        """
        stack = inspect.stack()
        pad = 0
        while True:
            filename = stack[pad].filename
            if "asyncio" in filename or os.path.basename(filename) == "logger.py":
                pad += 1
            else:
                break
        return pad

    @staticmethod
    def input(depth: int = 1):
        """
        Decorator to log the inputs passed into a function or coroutine.

        The function to decorate needs to be a method of an instance of a
        descendant of this class. Logs will be emitted using the instance's own
        logger.

        Normally, the input logs will be emitted before function execution. An
        exception is when this decorator is used on the __init__ function, in
        which case input logging has to be delayed until function return. The
        reason is the instance's logger does not exist prior to that point.

        Args:
            depth: The number of stack frames to skip when attributing the log.
                Useful when nested inside other decorators.
        """
        from src import env

        def decorator(func):

            is_init = func.__name__ == "__init__"
            is_async = inspect.iscoroutinefunction(func)
            func_sig = inspect.signature(func)

            if is_async:

                @functools.wraps(func)
                async def wrapped_async(*args, **kwargs):
                    self = args[0]
                    bound_args = func_sig.bind_partial(*args, **kwargs)
                    bound_args.apply_defaults()
                    func_args = {
                        k: v for k, v in bound_args.arguments.items() if k != "self"
                    }
                    if not is_init:
                        self.log.opt(depth=depth + Logger._get_async_pad()).log(
                            Logger._FUNC_INPUT_LEVEL_NAME,
                            Logger._FUNC_INPUT_MSG,
                            class_name=self.__class__.__name__,
                            func_name=func.__name__,
                            func_args=env.repr(func_args),
                        )
                    func_result = await func(*args, **kwargs)
                    if is_init:
                        self.log.opt(depth=depth + Logger._get_async_pad()).log(
                            Logger._FUNC_INPUT_LEVEL_NAME,
                            Logger._FUNC_INPUT_MSG,
                            class_name=self.__class__.__name__,
                            func_name=func.__name__,
                            func_args=env.repr(func_args),
                        )
                    return func_result

                return wrapped_async

            else:

                @functools.wraps(func)
                def wrapped_func(*args, **kwargs):
                    self = args[0]
                    bound_args = func_sig.bind_partial(*args, **kwargs)
                    bound_args.apply_defaults()
                    func_args = {
                        k: v for k, v in bound_args.arguments.items() if k != "self"
                    }
                    if not is_init:
                        self.log.opt(depth=depth).log(
                            Logger._FUNC_INPUT_LEVEL_NAME,
                            Logger._FUNC_INPUT_MSG,
                            class_name=self.__class__.__name__,
                            func_name=func.__name__,
                            func_args=env.repr(func_args),
                        )
                    func_result = func(*args, **kwargs)
                    if is_init:
                        self.log.opt(depth=depth).log(
                            Logger._FUNC_INPUT_LEVEL_NAME,
                            Logger._FUNC_INPUT_MSG,
                            class_name=self.__class__.__name__,
                            func_name=func.__name__,
                            func_args=env.repr(func_args),
                        )
                    return func_result

                return wrapped_func

        return decorator

    @staticmethod
    def output(depth: int = 1):
        """
        Decorator to log the outputs returned from a function or coroutine.

        The function to decorate needs to be a method of an instance of a
        descendant of this class. Logs will be emitted using the instance's own
        logger.

        Args:
            depth: The number of stack frames to skip when attributing the log.
                Useful when nested inside other decorators.
        """
        from src import env

        def decorator(func):

            is_async = inspect.iscoroutinefunction(func)

            if is_async:

                @functools.wraps(func)
                async def wrapped_afunc(*args, **kwargs):
                    self = args[0]
                    func_result = await func(*args, **kwargs)
                    # +1 to achieve parity with input line num for coroutines
                    self.log.opt(depth=depth + Logger._get_async_pad() + 1).log(
                        Logger._FUNC_OUTPUT_LEVEL_NAME,
                        Logger._FUNC_OUTPUT_MSG,
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

                return wrapped_afunc

            else:

                @functools.wraps(func)
                def wrapped_func(*args, **kwargs):
                    self = args[0]
                    func_result = func(*args, **kwargs)
                    self.log.opt(depth=depth).log(
                        Logger._FUNC_OUTPUT_LEVEL_NAME,
                        Logger._FUNC_OUTPUT_MSG,
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

    @staticmethod
    def io(depth: int = 1):
        """
        Decorator to log both inputs and outputs of a function or coroutine.

        The function to decorate needs to be a method of an instance of a
        descendant of this class. Logs will be emitted using the instance's own
        logger.

        Normally, the input logs will be emitted before function execution. An
        exception is when this decorator is used on the __init__ function, in
        which case input logging has to be delayed until function return. The
        reason is the instance's logger does not exist prior to that point.

        Args:
            depth: The number of stack frames to skip when attributing the log.
                Useful when nested inside other decorators.
        """

        def decorator(func):
            return Logger.output(depth)(Logger.input(depth + 1)(func))

        return decorator
