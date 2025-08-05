"""Dependent util funcs that have dependencies in src."""

import rich.pretty

from src import env
from src.core.util import multiline


def logid2logspace(logid: str) -> list[str]:
    """Given a logid, return the logspace of the logger as a list."""
    return logid.split(env.LOGSPACE_LOGNAME_SEPARATOR)[0].split(env.LOGSPACE_DELIMITER)


def logid2logname(logid: str) -> str:
    """Given a logid, return the logname of the logger."""
    return logid.split(env.LOGSPACE_LOGNAME_SEPARATOR)[-1]


def produce_logid(logspace: list[str], logname: str) -> str:
    """Given a logspace and a logname, return the logid of the logger."""
    return multiline(
        f"""
        {env.LOGSPACE_DELIMITER.join(logspace)}
        {env.LOGSPACE_LOGNAME_SEPARATOR}
        {logname}
        """,
        continuous=True,
    )


def prepr(
    obj,
    *,
    max_width: int | None = None,
    indent: int | None = None,
):
    """Pretty repr an arbitrary object for str output, using env defaults."""
    return rich.pretty.pretty_repr(
        obj,
        max_width=max_width or env.MAX_LINELEN,
        indent_size=indent or env.INDENT,
        expand_all=True,
    )
