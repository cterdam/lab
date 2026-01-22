from enum import StrEnum

from src.core.logger import Logger
from src.core.util import (
    gid_t,
    logid_t,
    obj_id,
    obj_is_group,
    obj_name,
    obj_subkey,
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
        ADD = "ADD {relation} {member}"
        RM = "RM {relation} {member}"


class _Loggers(dict[str, _GroupLog]):
    """A default dict that maps group name to group logger."""

    def __missing__(self, name: str) -> _GroupLog:
        self[name] = _GroupLog(logname=name)
        return self[name]


_glog = _Loggers()

# OTHER UTIL ###################################################################


class Relation(StrEnum):
    """Types of membership relations."""

    INCLUDE = "include"
    EXCLUDE = "exclude"


def _membership_subkey(name: str, relation: Relation) -> str:
    """Get the Redis subkey for a group's relation set."""
    from src import env

    return obj_subkey(
        obj_id(env.GID_NAMESPACE, name),
        {
            Relation.INCLUDE: env.GROUP_INCLUDE_SUFFIX,
            Relation.EXCLUDE: env.GROUP_EXCLUDE_SUFFIX,
        }[relation],
    )


# API ##########################################################################


def add(groupname: str, member: logid_t | gid_t, relation: Relation) -> bool:
    """Add a relation between a group and a member."""
    from src import env

    result = env.r.sadd(_membership_subkey(groupname, relation), member) == 1
    if result:
        _glog[groupname].info(
            _GroupLog.logmsg.ADD.format(relation=relation, member=member)
        )
    return result


def rm(groupname: str, member: logid_t | gid_t, relation: Relation) -> bool:
    """Remove a relation between a group and a member."""
    from src import env

    result = env.r.srem(_membership_subkey(groupname, relation), member) == 1
    if result:
        _glog[groupname].info(
            _GroupLog.logmsg.RM.format(relation=relation, member=member)
        )
    return result


def children(groupname: str, relation: Relation) -> set[logid_t]:
    """Get immediate children of a group in a certain relation."""
    from src import env

    return env.r.smembers(_membership_subkey(groupname, relation))


def descendants(groupname: str) -> set[logid_t]:
    """Get all end members of a group via inheritance."""
    included, excluded = _resolve(groupname, visited=set())
    return included - excluded


def _resolve(groupname: str, visited: set[str]) -> tuple[set[logid_t], set[logid_t]]:
    """Resolve members recursively with cycle detection."""

    if groupname in visited:
        return set(), set()

    visited |= {groupname}
    included: set[logid_t] = set()
    excluded: set[logid_t] = set()

    for child in children(groupname, Relation.INCLUDE):
        if obj_is_group(child):
            inc_inc, inc_exc = _resolve(obj_name(child), visited)
            included |= inc_inc - inc_exc
        else:
            included.add(child)

    for child in children(groupname, Relation.EXCLUDE):
        if obj_is_group(child):
            exc_inc, exc_exc = _resolve(obj_name(child), visited)
            excluded |= exc_inc - exc_exc
        else:
            excluded.add(child)

    return included, excluded
