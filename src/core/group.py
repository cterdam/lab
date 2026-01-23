from enum import StrEnum

from src.core.logger import Logger
from src.core.util import (
    gid_t,
    logid_t,
    obj_id,
    obj_is_group,
    obj_name,
)

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
        RM = "RM {member}"


class _Loggers(dict[str, _GroupLog]):
    """A default dict that maps group name to group logger."""

    def __missing__(self, name: str) -> _GroupLog:
        self[name] = _GroupLog(logname=name)
        return self[name]


_glog = _Loggers()

# OTHER UTIL ###################################################################


def _group_key(groupname: str) -> str:
    """Get the Redis key for a group's membership ZSET."""
    from src import env

    return obj_id(env.GID_NAMESPACE, groupname)


# API ##########################################################################


def add(groupname: str, member: logid_t | gid_t, weight: float) -> None:
    """Add/update member with weight. Positive=include, negative=exclude."""
    from src import env

    env.r.zadd(_group_key(groupname), {member: weight})
    _glog[groupname].info(
        _GroupLog.logmsg.ADD.format(member=member, weight=weight)
    )


def rm(groupname: str, member: logid_t | gid_t) -> bool:
    """Remove member entirely."""
    from src import env

    result = env.r.zrem(_group_key(groupname), member) == 1
    if result:
        _glog[groupname].info(_GroupLog.logmsg.RM.format(member=member))
    return result


def children(groupname: str) -> dict[str, float]:
    """Get immediate children with their weights."""
    from src import env

    return dict(env.r.zrange(_group_key(groupname), 0, -1, withscores=True))


def descendants(groupname: str) -> dict[logid_t, float]:
    """Get all end members with resolved scores (positive only)."""
    scores = _resolve(groupname, visited=set())
    return {m: s for m, s in scores.items() if s > 0}


def _resolve(groupname: str, visited: set[str]) -> dict[logid_t, float]:
    """Resolve members recursively with cycle detection."""

    if groupname in visited:
        return {}

    visited |= {groupname}
    direct: dict[logid_t, float] = {}
    indirect: dict[logid_t, float] = {}

    for child, weight in children(groupname).items():
        if obj_is_group(child):
            for m, s in _resolve(obj_name(child), visited).items():
                if s > 0:
                    indirect[m] = indirect.get(m, 0) + weight * s
        else:
            direct[child] = weight

    return {**indirect, **direct}
