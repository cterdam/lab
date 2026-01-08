import atexit
import inspect
import os
import textwrap
from enum import StrEnum
from functools import cache, cached_property, wraps
from pathlib import Path
from typing import final

import loguru
from pydantic import BaseModel, Field
from pydantic_extra_types.color import Color
from redis.asyncio.client import Pipeline as AsyncPipeline
from redis.client import Pipeline

from src.core.util import REPO_ROOT, logid_t, multiline, prepr


class LogLevel(BaseModel):
    """Log level."""

    name: str = Field(
        min_length=1,
        description="Name of the logging level as its unique identifier",
    )

    no: int = Field(
        ge=1,
        description="Positive integer severity of the logging level.",
    )

    color: Color = Field(
        description="Color for the level's header in logs.",
    )


class Logger:
    """Overall base class for any traceable entity.

    Descendants own:

    - attributes:
        - logspace (list[str]):
            A list representing all names passed on to this logger from ancestor
            classes.
        - logname (str):
            Name of this logger, unique in its logspace.
        - logid (logid):
            A string ID for this instance for the purpose of logging, produced
            from its logspace and logname and unique across this run.
        - _log (loguru Logger):
            Underlying logger that logs with the instance's logid.

    - logging methods:
        - trace
        - debug
        - info
        - success
        - warning
        - error
        - critical

    - counter methods:
        - (a)(b)iget
        - (a)(b)iset
        - (a)incr

    Example use:
        >>> player.info(msg)
        >>> player.incr("win")

    Logs and counter info will be saved in files unique to the instance.

    This class also provides three decorators, which can be used to capture a
    function's input and output:
    - input
    - output
    - io

    When subclassing:
    - If providing a class attr `logspace_part`, logs of instances of the
      subclass will be stored down one hierarchy determined by this attr.
    - If overriding `def _logtag()`, logs of instances of the subclass will
      display short contextual info alongside the logid for log entries emitted
      with a non-empty return value for this func.
    - If having a custom logging level, it can be registered by calling
      `Logger.add_lvl`.
    - If having custom counter keys, these can be contained in a `coke` module.
    - If having custom logging msgs, these can be contained in a `logmsg`
      module.
    """

    # GENERAL ATTRIBUTES #######################################################

    # To be supplied by the instance during init
    logname: str

    # Each descendant class can add a layer in its log dir path by overriding
    logspace_part: str | None = None

    # Allow all logs for downstream sinks
    _LOG_LEVEL = 0

    # Default log format
    _LOG_FORMAT = (
        multiline(
            """
            <dim><green>{time:YYYY-MM-DD HH:mm:ss!UTC}</></>
            <level>[{level:^8}]</>
            <dim><cyan>{extra[logid]}{extra[logtag]}</></> |
            <dim><yellow>{extra[relpath]}:{line} <{function}></></>
            """
        )
        + "\n{message}"
    )

    # Add pad to stack trace depth for async func decorators
    _LOG_ASYNC_PAD = 6

    # Params for configuring log levels ----------------------------------------

    _func_input_lvl = LogLevel(name="FINP <-", no=7, color="38758A")  # type: ignore
    _func_output_lvl = LogLevel(name="FOUT ->", no=7, color="4A6FA5")  # type: ignore
    _counter_lvl = LogLevel(name="COUNT", no=9, color="DAA520")  # type: ignore

    # (lvl_name, lvl_no, lvl_fg, lvl_is_builtin) for each lvl
    _LOG_LVLS = [
        LogLevel(name="TRACE", no=5, color="#505050"),  # type: ignore
        _func_input_lvl,
        _func_output_lvl,
        _counter_lvl,
        LogLevel(name="DEBUG", no=10, color="C080D3"),  # type: ignore
        LogLevel(name="INFO", no=20, color="5FAFAC"),  # type: ignore
        LogLevel(name="SUCCESS", no=25, color="2E8B57"),  # type: ignore
        LogLevel(name="WARNING", no=30, color="E09C34"),  # type: ignore
        LogLevel(name="ERROR", no=40, color="E04E3A"),  # type: ignore
        LogLevel(name="CRITICAL", no=50, color="FF0000"),  # type: ignore
    ]

    # Special messages ---------------------------------------------------------

    class logmsg(StrEnum):

        # Function input logging
        FUNC_INPUT = multiline(
            """
            {class_name}.{func_name}(...) <-
            {func_args}
            """,
            oneline=False,
        )

        # Function output logging
        FUNC_OUTPUT = multiline(
            """
            {class_name}.{func_name}(...) ->
            {func_result}
            """,
            oneline=False,
        )

        # Counter logging
        COUNT_SET = "# [{counter_key}] <- ({set_val})"
        COUNT_INCR = "# [{counter_key}] += ({incr_val})"
        COUNT_TALLY = multiline(
            """
            Shutting down; Tallying counters.
            {counters}
            """,
            oneline=False,
        )

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

    @final
    @cached_property
    def logspace(self) -> list[str]:
        """The list of names passed down from ancestor classes."""
        return [
            logspace_part
            for cls in reversed(self.__class__.__mro__)
            if (logspace_part := cls.__dict__.get("logspace_part"))
        ]

    @final
    @cached_property
    def logspace_dir(self) -> Path:
        from src import env

        return env.log_dir.joinpath(*self.logspace)

    @final
    @cached_property
    def logid(self) -> logid_t:
        """A unique identifier of the logger."""
        from src import env

        return multiline(
            f"""
            {env.LOGSPACE_DELIMITER.join(self.logspace)}
            {env.LOGSPACE_LOGNAME_SEPARATOR}
            {self.logname}
            """,
            continuous=True,
        )

    @property
    def _logtag(self) -> str | None:
        """Return any contextual info for logging alongside the logid.

        If returning None, no contextual info will be displayed.
        """
        return None

    def __init__(self, *args, logname: str, **kwargs):
        """Initialize this instance's logger.

        Args:
            logname (str): Name for this instance's log files. Should be unique
                in this instance's logspace.
        """
        super().__init__(*args, **kwargs)
        from src import env

        # Bind logger for this instance
        self.logname = logname
        self._log = Logger._base_logger().bind(logid=self.logid)
        self._log = self._log.patch(
            lambda record: record["extra"].update(
                logtag=f" [{self._logtag}]" if self._logtag else ""
            )
        )

        # Check for duplicate logid
        if env.r.sadd(env.LOGID_SET_KEY, self.logid) == 0:
            self._log.warning(f"Duplicate logid: {self.logid}")

        # Add file sinks
        only_self = lambda record: record["extra"]["logid"] == self.logid
        Logger.add_sink(
            self.logspace_dir / f"{logname}.txt",
            filter=only_self,
            colorize=True,
        )

    @final
    @cache
    @staticmethod
    def _base_logger():
        """Set up and return the base logger.

        This function code will only run once as there is only one base logger
        in the loguru methodology. Subsequent calls will hit the functools.cache
        instead.

        All derivative loggers from this class should base on this logger."""

        # Use loguru logger
        logger = loguru.logger

        # Send relative path and header str with records
        logger = logger.patch(
            lambda record: record["extra"].update(
                relpath=os.path.relpath(record["file"].path, REPO_ROOT)
            )
        )

        # Configure logging levels with colorscheme
        for lvl in Logger._LOG_LVLS:
            Logger.add_lvl(lvl)

        return logger

    @final
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

    @final
    @staticmethod
    def remove_sink(sink_id: int) -> None:
        """Remove a previously added sink from the shared logger.

        Args:
            sink_id (int): The integer handle returned by `add_sink`.
        """
        Logger._base_logger().remove(sink_id)

    @final
    @staticmethod
    def add_lvl(lvl: LogLevel) -> None:
        """Register or change a log level."""
        logger = loguru.logger
        color = f"<bold><fg {lvl.color.as_hex(format='long')}>"

        try:
            # Existent level
            logger.level(name=lvl.name, color=color, icon="")
        except:
            # New level
            logger.level(name=lvl.name, no=lvl.no, color=color, icon="")

    # COUNTER ##################################################################

    @final
    @cached_property
    def chn(self) -> str:
        """Counter hash name. Name of the logger's counter hash in Redis."""
        return Logger.logid2chn(self.logid)

    @final
    @staticmethod
    def logid2chn(logid: str) -> str:
        """Given a logid, return its corresponding counter hash name."""
        from src import env

        return f"{logid}{env.LOGID_SUBKEY_SEPARATOR}{env.CHN_SUFFIX}"

    # - SYNCHRONOUS ------------------------------------------------------------

    @final
    def iget(self, k: str, *, p: Pipeline | None = None) -> int | None:
        """Int GET.

        Get a counter value by key under this logger, or None if key absent.

        If a pipeline is provided, includes the command as part of the pipeline.
        Note that in this case, the caller is responsible for executing the
        pipeline.
        """
        from src import env

        target = p or env.cr
        result = target.hget(
            name=self.chn,
            key=k,
        )
        return result  # type: ignore

    @final
    def biget(self, ks: list[str], *, p: Pipeline | None = None) -> list[int | None]:
        """Batch Int GET.

        Get a list of counter values by keys under this logger, or None for each
        absent key.
        If a pipeline is provided, executes the command as part of the pipeline.
        Note that in this case, the caller is responsible for executing the
        pipeline, and additionally converting the result to int.
        """
        from src import env

        target = p or env.cr
        result = target.hmget(
            name=self.chn,
            keys=ks,
        )
        return result  # type: ignore

    @final
    def iset(self, k: str, v: int | float, *, p: Pipeline | None = None) -> int:
        """Int SET.

        Set a counter value under this logger by key, regardless of prior value.
        If a pipeline is provided, executes the command as part of the pipeline.
        Note that in this case, the caller is responsible for executing the
        pipeline.
        """
        from src import env

        target = p or env.cr
        result = target.hset(
            name=self.chn,
            key=k,
            value=str(v),
        )

        self._log.opt(depth=1).log(
            Logger._counter_lvl.name,
            Logger.logmsg.COUNT_SET.format(
                counter_key=k,
                set_val=v,
            ),
        )

        return result  # type: ignore

    @final
    def biset(self, mapping: dict[str, int], *, p: Pipeline | None = None) -> int:
        """Batch Int SET.

        Set a list of counter values under this logger by keys, regardless of
        prior values.
        If a pipeline is provided, executes the command as part of the pipeline.
        Note that in this case, the caller is responsible for executing the
        pipeline.
        """
        from src import env

        target = p or env.cr
        result = target.hset(
            name=self.chn,
            mapping=mapping,  # type: ignore
        )

        self._log.opt(depth=1).log(
            Logger._counter_lvl.name,
            "\n".join(
                [
                    Logger.logmsg.COUNT_SET.format(counter_key=k, set_val=v)
                    for k, v in mapping.items()
                ]
            ),
        )

        return result  # type: ignore

    @final
    def incr(self, k: str, v: int = 1, *, p: Pipeline | None = None) -> int:
        """Int iNCRement.

        Increment a counter by key under this logger.
        If a pipeline is provided, executes the command as part of the pipeline.
        Note that in this case, the caller is responsible for executing the
        pipeline.
        """
        from src import env

        target = p or env.cr
        result = target.hincrby(self.chn, k, v)

        self._log.opt(depth=1).log(
            Logger._counter_lvl.name,
            Logger.logmsg.COUNT_INCR.format(
                counter_key=k,
                incr_val=v,
            ),
        )

        return result  # type: ignore

    # - ASYNCHRONOUS -----------------------------------------------------------

    @final
    async def aiget(self, k: str, *, p: AsyncPipeline | None = None) -> int | None:
        """Async Int GET.

        Get a counter value by key under this logger, or None if key absent.

        If a pipeline is provided, includes the command as part of the pipeline.
        Note that in this case, the caller is responsible for executing the
        pipeline.
        """
        from src import env

        target = p or env.acr
        result = await target.hget(  # type: ignore
            name=self.chn,
            key=k,
        )
        return result  # type: ignore

    @final
    async def abiget(
        self, ks: list[str], *, p: AsyncPipeline | None = None
    ) -> list[int | None]:
        """Async Batch Int GET.

        Get a list of counter values by keys under this logger, or None for each
        absent key.
        If a pipeline is provided, executes the command as part of the pipeline.
        Note that in this case, the caller is responsible for executing the
        pipeline, and additionally converting the result to int.
        """
        from src import env

        target = p or env.acr
        result = await target.hmget(  # type: ignore
            name=self.chn,
            keys=ks,
        )
        return result  # type: ignore

    @final
    async def aiset(
        self, k: str, v: int | float, *, p: AsyncPipeline | None = None
    ) -> int:
        """Async Int SET.

        Set a counter value under this logger by key, regardless of prior value.
        If a pipeline is provided, executes the command as part of the pipeline.
        Note that in this case, the caller is responsible for executing the
        pipeline.
        """
        from src import env

        target = p or env.acr
        result = await target.hset(  # type: ignore
            name=self.chn,
            key=k,
            value=str(v),
        )
        return result  # type: ignore

    @final
    async def abiset(
        self, mapping: dict[str, int], *, p: AsyncPipeline | None = None
    ) -> int:
        """Async Batch Int SET.

        Set a list of counter values under this logger by keys, regardless of
        prior values.
        If a pipeline is provided, executes the command as part of the pipeline.
        Note that in this case, the caller is responsible for executing the
        pipeline.
        """
        from src import env

        target = p or env.acr
        result = await target.hset(
            name=self.chn,
            mapping=mapping,  # type: ignore
        )
        return result  # type: ignore

    @final
    async def aincr(self, k: str, v: int = 1, *, p: AsyncPipeline | None = None) -> int:
        """Async Int iNCRement.

        Increment a counter by key under this logger.
        If a pipeline is provided, executes the command as part of the pipeline.
        Note that in this case, the caller is responsible for executing the
        pipeline.
        """
        from src import env

        target = p or env.acr
        result = await target.hincrby(self.chn, k, v)  # type: ignore

        self._log.opt(depth=1).log(
            Logger._counter_lvl.name,
            Logger.logmsg.COUNT_INCR.format(
                counter_key=k,
                incr_val=v,
            ),
        )

        return result  # type: ignore

    # - OTHERS -----------------------------------------------------------------

    @final
    @staticmethod
    @atexit.register
    def _dump_counters():
        """Dump all loggers' counters from this run in logs and JSON files."""
        from src import env

        if not env.cr.set(env.COUNTER_DUMP_LOCK_KEY, os.getpid(), nx=True):
            return  # Ensure only one process does this

        try:
            logids = list(env.r.smembers(env.LOGID_SET_KEY))  # type: ignore
            with env.coup() as p:
                for logid in logids:
                    p.hgetall(Logger.logid2chn(logid))
                counter_hashes = p.execute()

            for logid, counter_kvs in zip(logids, counter_hashes):
                if not counter_kvs:
                    continue
                msg = Logger.logmsg.COUNT_TALLY.format(counters=prepr(counter_kvs))

                # Send log entry
                Logger._base_logger().bind(logid=logid, logtag="").log(
                    Logger._counter_lvl.name,
                    msg,
                )

                # Dump to file
                logspace = logid.split(env.LOGSPACE_LOGNAME_SEPARATOR)[0].split(
                    env.LOGSPACE_DELIMITER
                )
                logspace_dir = env.log_dir.joinpath(*logspace)
                logspace_dir.mkdir(parents=True, exist_ok=True)
                logname = logid.split(env.LOGSPACE_LOGNAME_SEPARATOR)[-1]
                (logspace_dir / f"{logname}_counters.json").write_text(msg)

        finally:
            env.cr.delete(env.COUNTER_DUMP_LOCK_KEY)

    # FUNC CALL DECORATORS #####################################################

    @final
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
        from src.core.util import prepr

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
                        self._log.opt(depth=depth + Logger._LOG_ASYNC_PAD).log(
                            Logger._func_input_lvl.name,
                            Logger.logmsg.FUNC_INPUT.format(
                                class_name=self.__class__.__name__,
                                func_name=func.__name__,
                                func_args=prepr(func_args),
                            ),
                        )
                    func_result = await func(*args, **kwargs)
                    if is_init:
                        self._log.opt(depth=depth + Logger._LOG_ASYNC_PAD).log(
                            Logger._func_input_lvl.name,
                            Logger.logmsg.FUNC_INPUT.format(
                                class_name=self.__class__.__name__,
                                func_name=func.__name__,
                                func_args=prepr(func_args),
                            ),
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
                            Logger._func_input_lvl.name,
                            Logger.logmsg.FUNC_INPUT.format(
                                class_name=self.__class__.__name__,
                                func_name=func.__name__,
                                func_args=prepr(func_args),
                            ),
                        )
                    func_result = func(*args, **kwargs)
                    if is_init:
                        self._log.opt(depth=depth).log(
                            Logger._func_input_lvl.name,
                            Logger.logmsg.FUNC_INPUT.format(
                                class_name=self.__class__.__name__,
                                func_name=func.__name__,
                                func_args=prepr(func_args),
                            ),
                        )
                    return func_result

                return wrapped_func

        return decorator

    @final
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
        from src.core.util import prepr

        def decorator(func):

            is_async = inspect.iscoroutinefunction(func)

            if is_async:

                @wraps(func)
                async def wrapped_afunc(*args, **kwargs):
                    self = args[0]
                    func_result = await func(*args, **kwargs)
                    self._log.opt(depth=depth + Logger._LOG_ASYNC_PAD).log(
                        Logger._func_output_lvl.name,
                        Logger.logmsg.FUNC_OUTPUT.format(
                            class_name=self.__class__.__name__,
                            func_name=func.__name__,
                            func_result=textwrap.indent(
                                prepr(
                                    func_result,
                                    max_width=env.MAX_WIDTH - env.INDENT,
                                    indent=env.INDENT,
                                ),
                                prefix=" " * env.INDENT,
                            ),
                        ),
                    )
                    return func_result

                return wrapped_afunc

            else:

                @wraps(func)
                def wrapped_func(*args, **kwargs):
                    self = args[0]
                    func_result = func(*args, **kwargs)
                    self._log.opt(depth=depth).log(
                        Logger._func_output_lvl.name,
                        Logger.logmsg.FUNC_OUTPUT.format(
                            class_name=self.__class__.__name__,
                            func_name=func.__name__,
                            func_result=textwrap.indent(
                                prepr(
                                    func_result,
                                    max_width=env.MAX_WIDTH - env.INDENT,
                                    indent=env.INDENT,
                                ),
                                prefix=" " * env.INDENT,
                            ),
                        ),
                    )
                    return func_result

                return wrapped_func

        return decorator

    @final
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
