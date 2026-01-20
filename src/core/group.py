"""Redis-backed group membership management with per-group logging.

Groups are identified by gid (group ID) in format: g:groupname
Redis keys:
- {gid}/include: SET of included logids or gids
- {gid}/exclude: SET of excluded logids or gids

Groups are implicit - they exist if they have members.
Each group gets its own log file via internal Logger instances.
"""

from enum import StrEnum

from pydantic import Field

from src import env
from src.core.dataclass import Dataclass
from src.core.logger import Logger
from src.core.util import (
    get_obj_id,
    get_obj_subkey,
    gid_t,
    logid_t,
    obj2name,
    obj_in_namespace,
)


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


class _GroupLogger(Logger):
    """Internal Logger for per-group logging."""

    logspace_part = "group"


_loggers: dict[str, _GroupLogger] = {}


def _log(name: str) -> _GroupLogger:
    """Get or create a logger for a group."""
    if name not in _loggers:
        _loggers[name] = _GroupLogger(logname=name)
    return _loggers[name]


def _key(name: str, relation: Relation) -> str:
    """Redis key for a relation set."""
    suffix = (
        env.GID_INCLUDE_SUFFIX
        if relation == Relation.INCLUDE
        else env.GID_EXCLUDE_SUFFIX
    )
    return get_obj_subkey(gid(name), suffix)


# Public API


def gid(name: str) -> gid_t:
    """Get gid for a group name."""
    return get_obj_id(env.GID_PREFIX, name)


def add(name: str, member: logid_t | gid_t, relation: Relation) -> bool:
    """Add a relation between a group and a member."""
    result = env.r.sadd(_key(name, relation), member) == 1
    if result:
        _log(name).info(f"{relation}: {member}")
    return result


def rm(name: str, member: logid_t | gid_t, relation: Relation) -> bool:
    """Remove a relation between a group and a member."""
    result = env.r.srem(_key(name, relation), member) == 1
    if result:
        _log(name).info(f"rm {relation}: {member}")
    return result


def delete(name: str) -> int:
    """Delete group's include and exclude sets."""
    result = env.r.delete(
        _key(name, Relation.INCLUDE),
        _key(name, Relation.EXCLUDE),
    )
    if result:
        _log(name).info("deleted")
    return result


def members(name: str) -> set[logid_t]:
    """Get resolved members of a group."""
    included, excluded = _resolve(name, visited=set())
    return included - excluded


def has(name: str, member: logid_t) -> bool:
    """Check if member is in group."""
    return member in members(name)


def trace(name: str, member: logid_t) -> Trace:
    """Trace how a member relates to a group.

    Returns paths showing how the member is included/excluded,
    plus the final verdict.
    """
    paths = _trace_paths(name, member, steps=[], visited=set())
    has_include = any(
        p.steps[-1].relation == Relation.INCLUDE for p in paths if p.steps
    )
    has_exclude = any(
        p.steps[-1].relation == Relation.EXCLUDE for p in paths if p.steps
    )
    verdict = has_include and not has_exclude
    return Trace(paths=paths, verdict=verdict)


def _trace_paths(
    name: str,
    member: logid_t,
    steps: list[Step],
    visited: set[str],
) -> list[Path]:
    """Recursively trace paths to a member."""
    if name in visited:
        return []

    visited = visited | {name}
    paths: list[Path] = []

    for relation in Relation:
        for m in env.r.smembers(_key(name, relation)):
            current_steps = steps + [Step(group=name, relation=relation)]
            if m == member:
                paths.append(Path(steps=current_steps))
            elif obj_in_namespace(m, env.GID_PREFIX):
                paths.extend(
                    _trace_paths(obj2name(m), member, current_steps, visited)
                )

    return paths


def _resolve(name: str, visited: set[str]) -> tuple[set[logid_t], set[logid_t]]:
    """Resolve members recursively with cycle detection."""
    if name in visited:
        _log(name).warning("circular reference detected")
        return set(), set()

    visited = visited | {name}
    included: set[logid_t] = set()
    excluded: set[logid_t] = set()

    for member in env.r.smembers(_key(name, Relation.INCLUDE)):
        if obj_in_namespace(member, env.GID_PREFIX):
            inc, exc = _resolve(obj2name(member), visited)
            included |= inc
            excluded |= exc
        else:
            included.add(member)

    for member in env.r.smembers(_key(name, Relation.EXCLUDE)):
        if obj_in_namespace(member, env.GID_PREFIX):
            exc_inc, exc_exc = _resolve(obj2name(member), visited)
            excluded |= exc_inc - exc_exc
        else:
            excluded.add(member)

    return included, excluded
