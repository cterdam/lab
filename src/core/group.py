"""Redis-backed group membership management with per-group logging.

Groups are identified by gid (group ID) in format: g:groupname
Redis keys:
- {gid}/include: SET of included logids or gids
- {gid}/exclude: SET of excluded logids or gids

Groups are implicit - they exist if they have members.
Each group gets its own log file via internal Logger instances.
"""

from enum import StrEnum
from typing import NamedTuple

from src import env
from src.core.logger import Logger
from src.core.util import logid_t


class Relation(StrEnum):
    """Types of membership relations."""

    IN = "in"
    OUT = "out"


class Path(NamedTuple):
    """A path showing how a member relates to a group."""

    chain: list[str]  # Sequence of group names
    relation: Relation  # Type of relation


class Trace(NamedTuple):
    """Result of tracing a member's relationship to a group."""

    paths: list[Path]  # All paths found
    verdict: bool  # True if member is in group


class _GroupLogger(Logger):
    """Internal Logger for per-group logging."""

    logspace_part = "group"


_loggers: dict[str, _GroupLogger] = {}


def _log(name: str) -> _GroupLogger:
    """Get or create a logger for a group."""
    if name not in _loggers:
        _loggers[name] = _GroupLogger(logname=name)
    return _loggers[name]


def _gid(name: str) -> str:
    """Convert group name to gid."""
    return f"{env.GID_PREFIX}{env.NAMESPACE_OBJ_SEPARATOR}{name}"


def _in_key(name: str) -> str:
    """Redis key for include set."""
    return f"{_gid(name)}{env.OBJ_SUBKEY_SEPARATOR}{env.GID_INCLUDE_SUFFIX}"


def _out_key(name: str) -> str:
    """Redis key for exclude set."""
    return f"{_gid(name)}{env.OBJ_SUBKEY_SEPARATOR}{env.GID_EXCLUDE_SUFFIX}"


def _is_gid(s: str) -> bool:
    """Check if string is a gid."""
    return s.startswith(f"{env.GID_PREFIX}{env.NAMESPACE_OBJ_SEPARATOR}")


def _name_from_gid(gid: str) -> str:
    """Extract group name from gid."""
    prefix = f"{env.GID_PREFIX}{env.NAMESPACE_OBJ_SEPARATOR}"
    return gid[len(prefix):] if gid.startswith(prefix) else gid


# Public API


def gid(name: str) -> str:
    """Get gid for a group name."""
    return _gid(name)


def add(name: str, member: logid_t | str) -> bool:
    """Add member to group's include set."""
    result = env.r.sadd(_in_key(name), member) == 1
    if result:
        _log(name).info(f"in: {member}")
    return result


def rm(name: str, member: logid_t | str) -> bool:
    """Remove member from group's include set."""
    result = env.r.srem(_in_key(name), member) == 1
    if result:
        _log(name).info(f"rm: {member}")
    return result


def ban(name: str, member: logid_t | str) -> bool:
    """Add member to group's exclude set."""
    result = env.r.sadd(_out_key(name), member) == 1
    if result:
        _log(name).info(f"ban: {member}")
    return result


def unban(name: str, member: logid_t | str) -> bool:
    """Remove member from group's exclude set."""
    result = env.r.srem(_out_key(name), member) == 1
    if result:
        _log(name).info(f"unban: {member}")
    return result


def delete(name: str) -> int:
    """Delete group's include and exclude sets."""
    result = env.r.delete(_in_key(name), _out_key(name))
    if result:
        _log(name).info("deleted")
    return result


def list(name: str) -> set[logid_t]:
    """Get resolved members of a group."""
    included, excluded = _resolve(name, visited=set())
    return included - excluded


def has(name: str, member: logid_t) -> bool:
    """Check if member is in group."""
    return member in list(name)


def trace(name: str, member: logid_t) -> Trace:
    """Trace how a member relates to a group.

    Returns paths showing how the member is included/excluded,
    plus the final verdict.
    """
    paths = _trace_paths(name, member, chain=[], visited=set())
    has_in = any(p.relation == Relation.IN for p in paths)
    has_out = any(p.relation == Relation.OUT for p in paths)
    verdict = has_in and not has_out
    return Trace(paths=paths, verdict=verdict)


def _trace_paths(
    name: str,
    member: logid_t,
    chain: list[str],
    visited: set[str],
) -> list[Path]:
    """Recursively trace paths to a member."""
    if name in visited:
        return []

    visited = visited | {name}
    current_chain = chain + [name]
    paths: list[Path] = []

    # Check include set
    for m in env.r.smembers(_in_key(name)):
        if m == member:
            paths.append(Path(chain=current_chain, relation=Relation.IN))
        elif _is_gid(m):
            paths.extend(_trace_paths(
                _name_from_gid(m), member, current_chain, visited
            ))

    # Check exclude set
    for m in env.r.smembers(_out_key(name)):
        if m == member:
            paths.append(Path(chain=current_chain, relation=Relation.OUT))
        elif _is_gid(m):
            # Members included in excluded group become excluded
            sub_paths = _trace_paths(
                _name_from_gid(m), member, current_chain, visited
            )
            for p in sub_paths:
                if p.relation == Relation.IN:
                    paths.append(Path(chain=p.chain, relation=Relation.OUT))
                else:
                    paths.append(p)

    return paths


def _resolve(name: str, visited: set[str]) -> tuple[set[logid_t], set[logid_t]]:
    """Resolve members recursively with cycle detection."""
    if name in visited:
        _log(name).warning("circular reference detected")
        return set(), set()

    visited = visited | {name}
    included: set[logid_t] = set()
    excluded: set[logid_t] = set()

    for member in env.r.smembers(_in_key(name)):
        if _is_gid(member):
            inc, exc = _resolve(_name_from_gid(member), visited)
            included |= inc
            excluded |= exc
        else:
            included.add(member)

    for member in env.r.smembers(_out_key(name)):
        if _is_gid(member):
            exc_inc, exc_exc = _resolve(_name_from_gid(member), visited)
            excluded |= (exc_inc - exc_exc)
        else:
            excluded.add(member)

    return included, excluded
