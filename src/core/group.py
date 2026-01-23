from enum import StrEnum

from src.core.logger import Logger
from src.core.util import (
    gid_t,
    is_gid,
    logid_t,
    obj_name,
)

# CONSTANTS ####################################################################

INC = 1
EXC = -1

# GROUP LOGGING ################################################################


class _GroupLog(Logger):
    """Internal Logger for per-group logging.

    Since the ground truth of group membership is stored in Redis, each group is
    not typically managed by a dedicated Python object. Thus, special logger
    objects are created for group-specific logs.
    """

    logspace_part = "group"

    class logmsg(StrEnum):  # type: ignore
        ADD = "ADD {member} {weight}"
        RM = "RM {member} {weight}"


class _Loggers(dict[gid_t, _GroupLog]):
    """A default dict that maps gid to group logger."""

    def __missing__(self, gid: gid_t) -> _GroupLog:
        self[gid] = _GroupLog(logname=obj_name(gid))
        return self[gid]


_glog = _Loggers()

# API ##########################################################################


def add(gid: gid_t, member: logid_t | gid_t, weight: float = INC) -> None:
    """Add or update a member with weight."""
    from src import env

    env.r.zadd(gid, {member: weight})
    _glog[gid].info(_GroupLog.logmsg.ADD.format(member=member, weight=weight))


def rm(gid: gid_t, member: logid_t | gid_t) -> bool:
    """Remove a member entirely."""
    from src import env

    weight = env.r.zscore(gid, member)
    result = env.r.zrem(gid, member) == 1
    if result:
        _glog[gid].info(_GroupLog.logmsg.RM.format(member=member, weight=weight))
    return result


def children(gid: gid_t) -> dict[logid_t | gid_t, float]:
    """Get immediate children with their weights."""
    from src import env

    return dict(env.r.zrange(gid, 0, -1, withscores=True))


def descendants(
    gid: gid_t, visited: set[gid_t] | None = None
) -> dict[logid_t | gid_t, float]:
    """Resolve all members recursively"""

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
