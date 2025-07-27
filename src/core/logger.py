import asyncio
import atexit
import inspect
import os
import textwrap
from functools import cache, wraps
from threading import Thread
from typing import final

import loguru

from src.core.util import multiline


class Logger:
    """Overall base class for any entity that keeps its own log file.

    Descendants own:
    - logid (str): A string ID for this instance for the purpose of logging.
        This is unique across this run.
    - logging methods:
        - trace
        - debug
        - info
        - success
        - warning
        - error
        - critical

    Example use of logging methods:
    >>> player.info(msg)

    This class also provides three decorators:
    - input
    - output
    - io
    These can be used to capture a function's input and output.
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
            <dim><green>{time:YYYY-MM-DD HH:mm:ss!UTC}</></>
            <level>[{level:^8}]</>
            <dim><cyan>{extra[logid]}</></> |
            <dim><yellow>{extra[relpath]}:{line}</></>
            """
        )
        + "\n{message}"
    )

    # Params for configuring log levels and colorschemes
    _FUNC_INPUT_LVL_NAME = "FINP <-"
    _FUNC_OUTPUT_LVL_NAME = "FOUT ->"
    _COUNTER_LVL_NAME = "COUNT"
    _FUNC_INPUT_LVL_MSG = multiline(
        """
        {class_name}.{func_name}(...) <-
        {func_args}
        """,
        oneline=False,
    )
    _FUNC_OUTPUT_LVL_MSG = multiline(
        """
        {class_name}.{func_name}(...) ->
        {func_result}
        """,
        oneline=False,
    )
    # (lvl_name, lvl_no, lvl_fg, lvl_is_builtin) for each lvl
    _LOG_LVLS = [
        ("TRACE", 5, "#505050", True),
        (_FUNC_INPUT_LVL_NAME, 7, "#38758A", False),
        (_FUNC_OUTPUT_LVL_NAME, 8, "#4A6FA5", False),
        ("DEBUG", 10, "#C080D3", True),
        (_COUNTER_LVL_NAME, 15, "#DAA520", False),
        ("INFO", 20, "#5FAFAC", True),
        ("SUCCESS", 25, "#2E8B57", True),
        ("WARNING", 30, "#E09C34", True),
        ("ERROR", 40, "#E04E3A", True),
        ("CRITICAL", 50, "#FF0000", True),
    ]

    # LOGGING METHODS ##########################################################

    @final
    def trace(self, *args, **kwargs):
        self.log.trace(*args, **kwargs)

    @final
    def debug(self, *args, **kwargs):
        self.log.debug(*args, **kwargs)

    @final
    def info(self, *args, **kwargs):
        self.log.info(*args, **kwargs)

    @final
    def success(self, *args, **kwargs):
        self.log.success(*args, **kwargs)

    @final
    def warning(self, *args, **kwargs):
        self.log.warning(*args, **kwargs)

    @final
    def error(self, *args, **kwargs):
        self.log.error(*args, **kwargs)

    @final
    def critical(self, *args, **kwargs):
        self.log.critical(*args, **kwargs)

    # SETUP & TEARDOWN #########################################################

    def __init__(self, *args, logname: str, **kwargs):
        """Initialize this instance’s logger.

        Args:
            logname (str): Name for this instance’s log files. Should be unique
                in this instance's namespace.
        """

        # Lazy import to avoid circular import problem
        from src import env

        # Build up namespace from class hierarchy
        _namespace = [
            namespace_part
            for cls in reversed(self.__class__.__mro__)
            if (namespace_part := cls.__dict__.get("namespace_part"))
        ]

        # Bind unique logid and logger for this instance
        self.logid = f"{'.'.join(_namespace)}:{logname}" if _namespace else logname
        if self.logid in env.loggers:
            raise ValueError(f"Duplicate logid: {self.logid}")
        env.loggers[self.logid] = self
        self.log = Logger._base_logger().bind(logid=self.logid)

        # Add file sinks
        _namespace_dir = env.log_dir.joinpath(*_namespace)
        only_self = lambda record: record["extra"]["logid"] == self.logid
        Logger.add_sink(
            _namespace_dir / f"{logname}.txt",
            filter=only_self,
        )
        Logger.add_sink(
            _namespace_dir / f"{logname}.colo.txt",
            filter=only_self,
            colorize=True,
        )
        Logger.add_sink(
            _namespace_dir / f"{logname}.jsonl",
            filter=only_self,
            serialize=True,
        )

        super().__init__(*args, **kwargs)

    @staticmethod
    @cache
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
        logger = logger.patch(
            lambda record: record["extra"].update(
                relpath=os.path.relpath(record["file"].path, env.repo_root)
            )
        )

        # Configure logging levels with colorscheme
        for lvl_name, lvl_no, lvl_fg, lvl_is_builtin in Logger._LOG_LVLS:
            if lvl_is_builtin:
                # Builtin level, just change color and icon here
                logger.level(
                    name=lvl_name,
                    color=f"<bold><fg {lvl_fg}>",
                    icon="",
                )
            else:
                # Custom level, register severity here
                logger.level(
                    name=lvl_name,
                    no=lvl_no,
                    color=f"<bold><fg {lvl_fg}>",
                    icon="",
                )

        # Start logging event loop in daemon thread
        Thread(target=Logger._log_event_loop.run_forever, daemon=True).start()

        return logger

    @staticmethod
    @atexit.register
    def _flush_logs():
        """Flush all logs enqueued at async sinks upon program exit."""

        async def _await_logger_complete():
            await Logger._base_logger().complete()

        asyncio.run_coroutine_threadsafe(
            _await_logger_complete(), Logger._log_event_loop
        ).result()
        Logger._log_event_loop.call_soon_threadsafe(Logger._log_event_loop.stop)

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

    # DECORATORS ###############################################################

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

                @wraps(func)
                async def wrapped_async(*args, **kwargs):
                    self = args[0]
                    bound_args = func_sig.bind_partial(*args, **kwargs)
                    bound_args.apply_defaults()
                    func_args = {
                        k: v for k, v in bound_args.arguments.items() if k != "self"
                    }
                    if not is_init:
                        self.log.opt(depth=depth + Logger._get_async_pad()).log(
                            Logger._FUNC_INPUT_LVL_NAME,
                            Logger._FUNC_INPUT_LVL_MSG,
                            class_name=self.__class__.__name__,
                            func_name=func.__name__,
                            func_args=env.repr(func_args),
                        )
                    func_result = await func(*args, **kwargs)
                    if is_init:
                        self.log.opt(depth=depth + Logger._get_async_pad()).log(
                            Logger._FUNC_INPUT_LVL_NAME,
                            Logger._FUNC_INPUT_LVL_MSG,
                            class_name=self.__class__.__name__,
                            func_name=func.__name__,
                            func_args=env.repr(func_args),
                        )
                    return func_result

                return wrapped_async

            else:

                @wraps(func)
                def wrapped_func(*args, **kwargs):
                    self = args[0]
                    bound_args = func_sig.bind_partial(*args, **kwargs)
                    bound_args.apply_defaults()
                    func_args = {
                        k: v for k, v in bound_args.arguments.items() if k != "self"
                    }
                    if not is_init:
                        self.log.opt(depth=depth).log(
                            Logger._FUNC_INPUT_LVL_NAME,
                            Logger._FUNC_INPUT_LVL_MSG,
                            class_name=self.__class__.__name__,
                            func_name=func.__name__,
                            func_args=env.repr(func_args),
                        )
                    func_result = func(*args, **kwargs)
                    if is_init:
                        self.log.opt(depth=depth).log(
                            Logger._FUNC_INPUT_LVL_NAME,
                            Logger._FUNC_INPUT_LVL_MSG,
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

                @wraps(func)
                async def wrapped_afunc(*args, **kwargs):
                    self = args[0]
                    func_result = await func(*args, **kwargs)
                    # +1 to achieve parity with input line num for coroutines
                    self.log.opt(depth=depth + Logger._get_async_pad() + 1).log(
                        Logger._FUNC_OUTPUT_LVL_NAME,
                        Logger._FUNC_OUTPUT_LVL_MSG,
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

                @wraps(func)
                def wrapped_func(*args, **kwargs):
                    self = args[0]
                    func_result = func(*args, **kwargs)
                    self.log.opt(depth=depth).log(
                        Logger._FUNC_OUTPUT_LVL_NAME,
                        Logger._FUNC_OUTPUT_LVL_MSG,
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
