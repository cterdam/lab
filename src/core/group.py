from enum import StrEnum

from pydantic import Field

from src.core.dataclass import Dataclass
from src.core.logger import Logger
from src.core.util import (
    gid_t,
    logid_t,
    obj_id,
    obj_is_group,
    obj_name,
    obj_subkey,
)

# RELATION #####################################################################


class Relation(StrEnum):
    """Types of membership relations."""

    INCLUDE = "include"
    EXCLUDE = "exclude"


class Step(Dataclass):
    """A single step in a membership path."""

    group: str
    relation: Relation


class Path(Dataclass):
    """A path showing how a member relates to a group."""

    steps: list[Step] = Field(default_factory=list)


class Trace(Dataclass):
    """Result of tracing a member's relationship to a group."""

    paths: list[Path] = Field(default_factory=list)
    verdict: bool = False


# GROUP LOGGING ################################################################


class _GroupLog(Logger):
    """Internal Logger for per-group logging.

    Since the ground truth of group membership is stored in Redis, each group is
    not typically managed by a separate Python object. Thus, special logger
    objects are created for group-specific logs.
    """

    logspace_part = "group"

    class logmsg(StrEnum):
        ADD = "ADD {relation} {member}"
        RM = "RM {relation} {member}"
        RESOLVE = "Resolving members"
        CIRCULAR = "Circular reference detected"


class _Loggers(dict[str, _GroupLog]):
    """Auto-creating dict for group loggers."""

    def __missing__(self, name: str) -> _GroupLog:
        self[name] = _GroupLog(logname=name)
        return self[name]


_glog = _Loggers()

# OTHER UTIL ###################################################################


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


def members(groupname: str) -> set[logid_t]:
    """Get resolved members of a group."""
    _glog[groupname].info(_GroupLog.logmsg.RESOLVE)
    included, excluded = _resolve(groupname, visited=set())
    return included - excluded


def _resolve(groupname: str, visited: set[str]) -> tuple[set[logid_t], set[logid_t]]:
    """Resolve members recursively with cycle detection."""
    from src import env

    if groupname in visited:
        _glog[groupname].warning(_GroupLog.logmsg.CIRCULAR)
        return set(), set()

    visited |= {groupname}
    included: set[logid_t] = set()
    excluded: set[logid_t] = set()

    for member in env.r.smembers(_membership_subkey(groupname, Relation.INCLUDE)):
        if obj_is_group(member):
            # Include the resolved members of the nested group
            inc_inc, inc_exc = _resolve(obj_name(member), visited)
            included |= inc_inc - inc_exc
        else:
            included.add(member)

    for member in env.r.smembers(_membership_subkey(groupname, Relation.EXCLUDE)):
        if obj_is_group(member):
            exc_inc, exc_exc = _resolve(obj_name(member), visited)
            excluded |= exc_inc - exc_exc
        else:
            excluded.add(member)

    return included, excluded
