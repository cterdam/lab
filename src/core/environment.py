import importlib.util
from contextlib import contextmanager
from functools import cached_property
from pathlib import Path

import redis
from pydantic import ConfigDict, Field, computed_field

from src.core.data_core import DataCore
from src.core.util import multiline, randalnu, str2int


class Environment(DataCore):
    """Context info about the run which are not set by the user."""

    # For pydantic to allow non-Pydantic fields
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # REPO #####################################################################

    @computed_field
    @cached_property
    def repo_root(self) -> Path:
        """Root path of the repo.
        This is assumed to be the parent of the `src` folder.
        """
        module_spec = importlib.util.find_spec("src")
        if module_spec is None or module_spec.origin is None:
            raise ModuleNotFoundError("Could not locate src module.")
        src_path = Path(module_spec.origin).parent
        repo_root = src_path.parent
        return repo_root

    @cached_property
    def py_files_abs(self) -> list[Path]:
        """Absolute paths to all .py files in this repo."""
        return list(self.repo_root.rglob("*.py"))

    @cached_property
    def py_file_rel(self) -> list[str]:
        """Relative paths to all .py files in this repo, from repo root."""
        return [
            str(py_file.relative_to(self.repo_root)) for py_file in self.py_files_abs
        ]

    @computed_field
    @cached_property
    def run_name(self) -> str:
        """Name of the current run."""
        # Lazy import to avoid circular import problem
        from src import arg

        if arg.run_name:
            return arg.run_name
        else:
            import getpass
            from datetime import datetime, timezone

            username: str = getpass.getuser()[:4]
            timedate: str = datetime.now(timezone.utc).strftime("%y%m%d-%H%M%S")
            randhash: str = randalnu(4)
            uniqueid: str = f"{username}-{timedate}-{randhash}"
            return uniqueid

    @computed_field
    @cached_property
    def out_dir(self) -> Path:
        """Dir to hold all outputs of the current run."""
        return self.repo_root / "out" / self.run_name

    @computed_field
    @cached_property
    def log_dir(self) -> Path:
        """Dir to hold all logs of the run."""
        return self.out_dir / "log"

    # FORMAT ###################################################################

    INDENT: int = Field(
        default=4,
        gt=0,
        description=multiline(
            """
            Default indentation for string formatting.
            """
        ),
    )

    MAX_WIDTH: int = Field(
        default=80,
        gt=0,
        description=multiline(
            """
            Maximum line length for string formatting.
            """
        ),
    )

    # LOG ######################################################################

    LOGSPACE_DELIMITER: str = Field(
        default=".",
        min_length=1,
        description=multiline(
            """
            Str delimiter between different parts of a logger's logspace when
            representing them in a logid.
            """
        ),
    )

    LOGSPACE_LOGNAME_SEPARATOR: str = Field(
        default=":",
        min_length=1,
        description=multiline(
            """
            Str connector between a logger's logspace and logname when
            representing them in a logid.
            """
        ),
    )

    ROOT_LOGNAME: str = Field(
        default="root",
        min_length=1,
        description=multiline(
            """
            logid for the root logger available as src.log
            """
        ),
    )

    # REDIS ####################################################################

    @cached_property
    def r_pool(self) -> redis.ConnectionPool:
        """Shared connection pool for redis clients."""
        from src import arg

        return redis.ConnectionPool.from_url(
            url=str(arg.REDIS_URL), decode_responses=True
        )

    @cached_property
    def r(self) -> redis.Redis:
        """Synchronous default redis client."""

        client = redis.Redis(connection_pool=self.r_pool)
        return client

    @cached_property
    def cr(self) -> redis.Redis:
        """Synchronous redis client for counters."""

        client = redis.Redis(connection_pool=self.r_pool)

        # Convert string results to int for counter gets.
        client.set_response_callback("HGET", str2int)
        client.set_response_callback("HMGET", lambda r: [str2int(v) for v in r])

        return client

    @contextmanager
    def coup(self, *, transaction: bool = False):
        """COunter UPdates.

        Context manager to send a batch of counter updates to Redis.
        When using this context manager, executing this pipeline is optional,
        because any remaining commands will be executed at context exit.
        This is different from when using a redis pipeline by itself.

        Example use:
        >>> from src import env, log
        >>> with env.coup() as p:
        ...     log.incr("k1", v, p=p)
        ...     log.incr("k2", v, p=p)

        """

        p = self.cr.pipeline(transaction=transaction)
        try:
            yield p
            if p.command_stack:
                p.execute()  # Flush any leftover cmds at context exit
        finally:
            p.reset()

    LOGID_SET_KEY: str = Field(
        default="logids",
        min_length=1,
        description=multiline(
            """
            Redis key to retrieve the set of all logids.
            """
        ),
    )

    CHN_SUFFIX: str = Field(
        default="counters",
        min_length=1,
        description=multiline(
            """
            Counter hash name suffix. String suffix to prepend to a logger's
            logid to form its counter hash name in Redis.
            """
        ),
    )

    LOGID_CHNS_SEPARATOR: str = Field(
        default="/",
        min_length=1,
        description=multiline(
            """
            Str connector between a logger's logid and the counter hash name
            suffix when producing the counter key.
            """
        ),
    )

    COUNTER_DUMP_LOCK_KEY: str = Field(
        default="counter_dump_lock",
        min_length=1,
        description=multiline(
            """
            Redis key to act as a lock for the final counter dump.
            """
        ),
    )
