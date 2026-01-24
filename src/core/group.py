from enum import StrEnum

from src.core.logger import Logger
from src.core.util import (
    gid_t,
    is_gid,
    logid_t,
    obj_name,
)

# CONSTANTS ####################################################################

# Canonical value for fully included members
INC = 1

# Canonical value for fully excluded members
EXC = -1

# GROUP LOGGING ################################################################


class _GroupLogger(Logger):
    """Internal Logger for per-group logging.

    Since the ground truth of group membership is stored in Redis, each group is
    not typically managed by a dedicated Python object. Thus, special logger
    objects are created for group-specific logs.
    """

    logspace_part = "group"

    class logmsg(StrEnum):  # type: ignore
        ADD = "ADD {member} {weight} -> {result}"
        RM = "RM {member} {weight} -> {result}"


class _GroupLoggers(dict[gid_t, _GroupLogger]):
    """A default dict that maps gid to group logger."""

    def __missing__(self, gid: gid_t) -> _GroupLogger:
        self[gid] = _GroupLogger(logname=obj_name(gid))
        return self[gid]


_glog = _GroupLoggers()

# API ##########################################################################


def add(gid: gid_t, member: logid_t | gid_t, weight: float = INC) -> bool:
    """Add or update a member with weight.

    Returns:
        Whether the add operation was successful.
    """
    from src import env

    # Check args
    assert is_gid(gid)

    # Clamp weight
    clamped_weight = max(-1.0, min(1.0, weight))
    if clamped_weight != weight:
        _glog[gid].warning(
            f"Weight clamped from {weight} to {clamped_weight} for member {member}"
        )

    # Add member
    result = env.r.zadd(gid, {member: clamped_weight})
    _glog[gid].info(
        _GroupLogger.logmsg.ADD.format(
            member=member,
            weight=clamped_weight,
            result=result,
        )
    )
    return bool(result)


def rm(gid: gid_t, member: logid_t | gid_t) -> bool:
    """Remove a member entirely.

    Returns:

    """
    from src import env

    assert is_gid(gid)

    result = env.r.zrem(gid, member)
    _glog[gid].info(
        _GroupLogger.logmsg.RM.format(
            member=member,
            weight=env.r.zscore(gid, member),
            result=result,
        )
    )
    return bool(result)


def children(gid: gid_t) -> dict[logid_t | gid_t, float]:
    """Get immediate children with weights of a group."""
    from src import env

    assert is_gid(gid)
    return dict(env.r.zrange(gid, 0, -1, withscores=True))


def descendants(
    gid: gid_t, visited: set[gid_t] | None = None
) -> dict[logid_t | gid_t, float]:
    """Resolve all direct and indirect members recursively."""

    assert is_gid(gid)

    if visited is None:
        visited = set()

    if gid in visited:
        return {}

    visited |= {gid}
    direct: dict[logid_t | gid_t, float] = {}
    indirect: dict[logid_t | gid_t, float] = {}

    for child, weight in children(gid).items():
        direct[child] = weight
        if is_gid(child):
            for m, s in descendants(child, visited).items():
                if s > 0:
                    indirect[m] = indirect.get(m, 0) + weight * s

    return {**indirect, **direct}
