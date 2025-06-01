import asyncio
import atexit
import functools
import inspect
import os
import textwrap
import threading
from typing import Any, Dict

import loguru

from src.core.util import multiline


class Logger:
    """Overall base class for an object that keeps its own log file.

    Descendants inherit self.log, a logger bound to a unique logger_id. This
    can be used to write logs to stdout and keeps its own file sink.
        E.g. `player.log.info(msg)`

    This class also provides three decorators: input(), output(), and io(), for
    logging a function's input and output.
    """

    # Each descendant class can add a layer in its log dir path by overriding
    namespace_part: str | None = None

    # Event loop to manage all logging async sinks, run in a separate thread.
    _log_event_loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()

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
    _BUILTIN_LEVEL_NAMES = [
        "TRACE",
        "DEBUG",
        "INFO",
        "SUCCESS",
        "WARNING",
        "ERROR",
        "CRITICAL",
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
        """Initialize this instance's logger.

        Args:
            log_name (str): Unique name for this instance's log files.
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
            filter=only_self,
        )
        Logger.add_sink(
            _namespace_dir / f"{log_name}.jsonl",
            filter=only_self,
            serialize=True,
        )

        super().__init__(*args, **kwargs)

    def __getattr__(self, name):
        """Default any attrs not overridden in this class to loguru logger."""
        return getattr(self.log, name)

    # SETUP & TEARDOWN #########################################################

    @staticmethod
    @functools.cache
    def _base_logger():
        """Set up and return the base logger.

        This function code will only run once as there is only one base logger
        in the loguru methodology. Subsequent calls will hit the functools.cache
        instead.

        All derivative loggers from this class should base on this logger."""

        from src import env

        # Use loguru logger
        logger = loguru.logger

        # Send relative path and header str with records
        logger = logger.patch(Logger._patch_relpath)

        # Configure logging levels with colorscheme
        for name, no, fg in Logger._LEVELS:
            if name in Logger._BUILTIN_LEVEL_NAMES:
                # Builtin level, just change color and icon here
                logger.level(
                    name=name,
                    color=f"<bold><fg {fg}>",
                    icon="",
                )
            else:
                # Custom level, register severity here
                logger.level(
                    name=name,
                    no=no,
                    color=f"<bold><fg {fg}>",
                    icon="",
                )

        # Start logging event loop in daemon thread
        threading.Thread(target=Logger._log_event_loop.run_forever, daemon=True).start()

        return logger

    @staticmethod
    @atexit.register
    def _flush_logs():
        """Flush all logs enqueued at async sinks upon program exit."""
        try:
            # Create a local reference to avoid NameError during shutdown
            base_logger = Logger._base_logger()
            event_loop = Logger._log_event_loop

            async def _await_logger_complete():
                await base_logger.complete()

            # Check if event loop is still running
            if not event_loop.is_closed():
                try:
                    asyncio.run_coroutine_threadsafe(
                        _await_logger_complete(), event_loop
                    ).result(
                        timeout=1.0
                    )  # Add timeout to prevent hanging
                    event_loop.call_soon_threadsafe(event_loop.stop)
                except Exception:
                    # Ignore errors during shutdown
                    pass
        except Exception:
            # Ignore all errors during shutdown to prevent noise
            pass

    @staticmethod
    def add_sink(sink, *args, **kwargs) -> int:
        """Attach a sink to the underlying shared Loguru logger.

        Returns:
            An integer sink ID, which can later be used to remove the sink.
        """
        kwargs.setdefault("level", Logger._LOG_LEVEL)
        kwargs.setdefault("format", Logger._LOG_FORMAT)
        kwargs["enqueue"] = True
        if inspect.iscoroutinefunction(sink):
            kwargs["loop"] = Logger._log_event_loop

        return Logger._base_logger().add(sink, *args, **kwargs)

    @staticmethod
    def remove_sink(sink_id: int) -> None:
        """Remove a previously added sink from the shared logger.

        Args:
            sink_id (int): The integer handle returned by `add_sink`.
        """
        Logger._base_logger().remove(sink_id)

    @staticmethod
    def _filter_by_id(record: Dict[str, Any], logger_id: str):
        """Loguru filter to only allow records matching the given logger_id"""
        return record["extra"]["logger_id"] == logger_id

    @staticmethod
    def _patch_relpath(record: Dict[str, Any]) -> None:
        """Loguru patch to add an extra field for relative path."""
        from src import env

        try:
            record["extra"]["relpath"] = os.path.relpath(
                record["file"].path, env.repo_root
            )
        except ValueError:
            # Handle cross-drive paths on Windows (e.g., C: vs D:)
            # Fall back to just the filename when drives differ
            record["extra"]["relpath"] = os.path.basename(record["file"].path)

    @staticmethod
    def _patch_header(record: Dict[str, Any]) -> None:
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

    @staticmethod
    def _get_async_pad() -> int:
        """Helper for func input output decorators to find depth pad number.

        Inspect the current call stack and, beyond the decorator wrapper itself,
        skip over any asyncio internals so that logs attribute correctly to the
        user's call site for a coroutine.
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
