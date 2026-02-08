import os
import weakref
from contextlib import asynccontextmanager, contextmanager
from functools import cached_property
from pathlib import Path
from typing import Any

import redis
import redis.asyncio
from pydantic import BaseModel, ConfigDict, Field, computed_field

from src.core.util import REPO_ROOT, Lid, multiline, str2int


class Environment(BaseModel):
    """Context info about the run which are not set by the user."""

    # For pydantic to allow non-Pydantic fields
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # REPO #####################################################################

    @computed_field
    @cached_property
    def run_id(self) -> str:
        """Unique identifier for the current run."""
        return os.environ["RUN_ID"]

    @computed_field
    @cached_property
    def redis_insight(self) -> str:
        """URL for RedisInsight."""
        return f"http://{os.environ['REDIS_INSIGHT']}"

    @computed_field
    @cached_property
    def out_dir(self) -> Path:
        """Dir to hold all outputs of the current run."""
        return REPO_ROOT / "out" / self.run_id

    @computed_field
    @cached_property
    def log_dir(self) -> Path:
        """Dir to hold all logs of the run."""
        return self.out_dir / "log"

    # FORMAT ###################################################################

    INDENT: int = Field(
        default=4,
        gt=0,
        description="Default indentation for string formatting.",
    )

    MAX_WIDTH: int = Field(
        default=80,
        gt=0,
        description="Maximum line length for string formatting.",
    )

    NAMESPACE_DELIMITER: str = Field(
        default=".",
        min_length=1,
        description=multiline(
            """
            Str delimiter between different parts of a namespace, e.g. a
            logger's logspace.
            """,
        ),
    )

    NAMESPACE_OBJ_SEPARATOR: str = Field(
        default=":",
        min_length=1,
        description=multiline(
            """
            Separator between a namespace and a member object in that namespace,
            e.g. between a logger's logspace and its logname.
            """,
        ),
    )

    OBJ_SUBKEY_SEPARATOR: str = Field(
        default="/",
        min_length=1,
        description="Str connector between a obj's ID and its subkeys.",
    )

    # REDIS ####################################################################

    # - SYNCHRONOUS ------------------------------------------------------------

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
        client.set_response_callback(
            "HGETALL",
            lambda r: (
                {k: str2int(v) for k, v in zip(r[::2], r[1::2])}
                if isinstance(r, list)
                else {k: str2int(v) for k, v in r.items()}
            ),
        )

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

    # - ASYNCHRONOUS -----------------------------------------------------------

    @cached_property
    def ar_pool(self) -> redis.asyncio.ConnectionPool:
        """Shared connection pool for async redis clients."""
        from src import arg

        return redis.asyncio.ConnectionPool.from_url(
            url=str(arg.REDIS_URL), decode_responses=True
        )

    @cached_property
    def ar(self) -> redis.asyncio.Redis:
        """Asynchronous default redis client."""

        client = redis.asyncio.Redis(connection_pool=self.ar_pool)
        return client

    @cached_property
    def acr(self) -> redis.asyncio.Redis:
        """Asynchronous redis client for counters."""

        client = redis.asyncio.Redis(connection_pool=self.ar_pool)

        # Convert string results to int for counter gets.
        client.set_response_callback("HGET", str2int)  # type: ignore
        client.set_response_callback(
            "HMGET", lambda r: [str2int(v) for v in r]  # type: ignore
        )
        client.set_response_callback(
            "HGETALL",
            lambda r: (  # type: ignore
                {k: str2int(v) for k, v in zip(r[::2], r[1::2])}
                if isinstance(r, list)
                else {k: str2int(v) for k, v in r.items()}
            ),
        )

        return client

    @asynccontextmanager
    async def acoup(self, *, transaction: bool = False):
        """Async COunter UPdates.

        Context manager to send a batch of counter updates to Redis.
        When using this context manager, executing this pipeline is optional,
        because any remaining commands will be executed at context exit.
        This is different from when using a redis pipeline by itself.

        Example use:
        >>> from src import env, log
        >>> async with env.acoup() as p:
        ...     await log.aincr("k1", v, p=p)
        ...     await log.aincr("k2", v, p=p)

        """

        p = self.acr.pipeline(transaction=transaction)
        try:
            yield p
            if p.command_stack:
                await p.execute()
        finally:
            await p.reset()

    # LOG ######################################################################

    # Mapping from lid to alive Logger objects.
    loggers: weakref.WeakValueDictionary[Lid, Any] = weakref.WeakValueDictionary()

    # Set of all lids created in this run (in this process).
    lids: set[Lid] = set()

    ROOT_LOGNAME: Lid = Field(
        default="root",
        min_length=1,
        description="lid for the root logger available as src.log",
    )

    COUNTER_HASH_SUFFIX: str = Field(
        default="counters",
        min_length=1,
        description=multiline(
            """
            Counter hash suffix. String suffix to prepend to a logger's
            lid to form its counter hash name in Redis.
            """
        ),
    )

    COUNTER_DUMP_LOCK_KEY: str = Field(
        default="counter_dump_lock",
        min_length=1,
        description="Redis key to act as a lock for the final counter dump.",
    )

    # SERIAL ID ################################################################

    SID_COUNTER_KEY: str = Field(
        default="sid",
        min_length=1,
        description=multiline(
            """
            Counter key for the globally shared serial ID generator. This ID is
            used as a global Redis counter for monotonically increasing IDs
            shared between different classes.
            """
        ),
    )

    # GROUP ####################################################################

    GID_NAMESPACE: str = Field(
        default="g",
        min_length=1,
        description="Prefix for group IDs.",
    )
