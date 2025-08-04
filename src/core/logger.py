import atexit
import inspect
import os
import textwrap
import time
from functools import cache, wraps
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
    - counter methods:
        - incr

    Example use:
    >>> player.info(msg)
    >>> player.incr("win")


    This class also provides three decorators:
    - input
    - output
    - io
    These can be used to capture a function's input and output.
    """

    # Each descendant class can add a layer in its log dir path by overriding
    namespace_part: str | None = None

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
        {class_name}.{func_name}(...) -> {elapsed_time} ->
        {func_result}
        """,
        oneline=False,
    )
    _COUNTER_LVL_MSG = multiline(
        """
        # [{counter_key}] += ({incr_val})
        """
    )
    # (lvl_name, lvl_no, lvl_fg, lvl_is_builtin) for each lvl
    _LOG_LVLS = [
        ("TRACE", 5, "#505050", True),
        (_FUNC_INPUT_LVL_NAME, 7, "#38758A", False),
        (_FUNC_OUTPUT_LVL_NAME, 8, "#4A6FA5", False),
        (_COUNTER_LVL_NAME, 9, "#DAA520", False),
        ("DEBUG", 10, "#C080D3", True),
        ("INFO", 20, "#5FAFAC", True),
        ("SUCCESS", 25, "#2E8B57", True),
        ("WARNING", 30, "#E09C34", True),
        ("ERROR", 40, "#E04E3A", True),
        ("CRITICAL", 50, "#FF0000", True),
    ]

    # LOGGING METHODS ##########################################################

    @final
    def trace(self, *args, **kwargs):
        self._log.opt(depth=1).trace(*args, **kwargs)

    @final
    def debug(self, *args, **kwargs):
        self._log.opt(depth=1).debug(*args, **kwargs)

    @final
    def info(self, *args, **kwargs):
        self._log.opt(depth=1).info(*args, **kwargs)

    @final
    def success(self, *args, **kwargs):
        self._log.opt(depth=1).success(*args, **kwargs)

    @final
    def warning(self, *args, **kwargs):
        self._log.opt(depth=1).warning(*args, **kwargs)

    @final
    def error(self, *args, **kwargs):
        self._log.opt(depth=1).error(*args, **kwargs)

    @final
    def critical(self, *args, **kwargs):
        self._log.opt(depth=1).critical(*args, **kwargs)

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
        existent = env.r.sadd(env.LOGGERS_SET_KEY, self.logid) == 0
        if self.logid != env.ROOT_LOGID and existent:
            raise ValueError(f"Duplicate logid: {self.logid}")
        self._log = Logger._base_logger().bind(logid=self.logid)

        # Add file sinks
        self.namespace_dir = env.log_dir.joinpath(*_namespace)
        only_self = lambda record: record["extra"]["logid"] == self.logid
        Logger.add_sink(
            self.namespace_dir / f"{logname}.txt",
            filter=only_self,
        )
        Logger.add_sink(
            self.namespace_dir / f"{logname}.colo.txt",
            filter=only_self,
            colorize=True,
        )
        Logger.add_sink(
            self.namespace_dir / f"{logname}.jsonl",
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

        return logger

    @staticmethod
    def add_sink(sink, *args, **kwargs) -> int:
        """Attach a sink to the underlying shared Loguru logger.

        Returns:
            An integer sink ID, which can later be used to remove the sink.
        """
        kwargs.setdefault("level", Logger._LOG_LEVEL)
        kwargs.setdefault("format", Logger._LOG_FORMAT)
        kwargs["enqueue"] = True
        return Logger._base_logger().add(sink, *args, **kwargs)

    @staticmethod
    def remove_sink(sink_id: int) -> None:
        """Remove a previously added sink from the shared logger.

        Args:
            sink_id (int): The integer handle returned by `add_sink`.
        """
        Logger._base_logger().remove(sink_id)

    # COUNTER ##################################################################

    def incr(self, key: str, val: int = 1) -> int:
        from src import env

        result = env.r.hincrby(f"{self.logid}/{env.COUNTER_KEY_SUFFIX}", key, val)

        self._log.opt(depth=1).log(
            Logger._COUNTER_LVL_NAME,
            Logger._COUNTER_LVL_MSG,
            counter_key=key,
            incr_val=val,
        )

        return result  # pyright:ignore

    @atexit.register
    @staticmethod
    def _dump_counters():
        """Dump all loggers' counters from this run in logs and JSON files."""
        from src import env

        if not env.r.set(env.COUNTER_DUMP_LOCK_KEY, os.getpid(), nx=True):
            # Ensure only one process does this
            return

        try:
            logids = list(env.r.smembers(env.LOGGERS_SET_KEY))  # pyright:ignore
            with env.r.pipeline() as pipe:
                for logid in logids:
                    pipe.hgetall(f"{logid}/{env.COUNTER_KEY_SUFFIX}")
                counter_collections = pipe.execute()

            for logid, counters in zip(logids, counter_collections):
                if not counters:
                    continue
                counters_repr = env.repr({k: int(v) for k, v in counters.items()})

                # Send log entry
                Logger._base_logger().bind(logid=logid).log(
                    Logger._COUNTER_LVL_NAME,
                    counters_repr,
                )

                # Dump to file
                namespace_dir = env.log_dir.joinpath(*logid.split(".")[:-1])
                namespace_dir.mkdir(parents=True, exist_ok=True)
                (namespace_dir / f"{logid}_counters.json").write_text(counters_repr)

        finally:
            env.r.delete(env.COUNTER_DUMP_LOCK_KEY)

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
                        self._log.opt(depth=depth + Logger._get_async_pad()).log(
                            Logger._FUNC_INPUT_LVL_NAME,
                            Logger._FUNC_INPUT_LVL_MSG,
                            class_name=self.__class__.__name__,
                            func_name=func.__name__,
                            func_args=env.repr(func_args),
                        )
                    func_result = await func(*args, **kwargs)
                    if is_init:
                        self._log.opt(depth=depth + Logger._get_async_pad()).log(
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
                        self._log.opt(depth=depth).log(
                            Logger._FUNC_INPUT_LVL_NAME,
                            Logger._FUNC_INPUT_LVL_MSG,
                            class_name=self.__class__.__name__,
                            func_name=func.__name__,
                            func_args=env.repr(func_args),
                        )
                    func_result = func(*args, **kwargs)
                    if is_init:
                        self._log.opt(depth=depth).log(
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
                    start_time = time.perf_counter()
                    func_result = await func(*args, **kwargs)
                    end_time = time.perf_counter()
                    # +1 to achieve parity with input line num for coroutines
                    self._log.opt(depth=depth + Logger._get_async_pad() + 1).log(
                        Logger._FUNC_OUTPUT_LVL_NAME,
                        Logger._FUNC_OUTPUT_LVL_MSG,
                        class_name=self.__class__.__name__,
                        func_name=func.__name__,
                        elapsed_time=f"{(end_time - start_time):.4f}s",
                        func_result=textwrap.indent(
                            env.repr(
                                func_result,
                                max_width=env.MAX_LINELEN - env.INDENT,
                                indent=env.INDENT,
                            ),
                            prefix=" " * env.INDENT,
                        ),
                    )
                    return func_result

                return wrapped_afunc

            else:

                @wraps(func)
                def wrapped_func(*args, **kwargs):
                    self = args[0]
                    start_time = time.perf_counter()
                    func_result = func(*args, **kwargs)
                    end_time = time.perf_counter()
                    self._log.opt(depth=depth).log(
                        Logger._FUNC_OUTPUT_LVL_NAME,
                        Logger._FUNC_OUTPUT_LVL_MSG,
                        class_name=self.__class__.__name__,
                        func_name=func.__name__,
                        elapsed_time=f"{(end_time - start_time):.4f}s",
                        func_result=textwrap.indent(
                            env.repr(
                                func_result,
                                max_width=env.MAX_LINELEN - env.INDENT,
                                indent=env.INDENT,
                            ),
                            prefix=" " * env.INDENT,
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
