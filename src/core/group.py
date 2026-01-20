"""Redis-backed group membership management.

Groups are identified by gid (group ID) in format: g:groupname
- The prefix "g" and separator ":" are configurable in env.

Redis keys:
- {gid}/in: SET of included logids (groups or members)
- {gid}/out: SET of excluded logids (groups or members)

Groups are implicit - they exist if they have members in include/exclude sets.

Resolution: included - excluded, with recursive expansion for nested groups.
"""

from src import env
from src.core.util import gid_t, logid_t


def gid(name: str) -> gid_t:
    """Get the gid for a group name."""
    return f"{env.GID_PREFIX}{env.GID_SEPARATOR}{name}"


def _name(g: gid_t) -> str:
    """Extract group name from a gid."""
    prefix = f"{env.GID_PREFIX}{env.GID_SEPARATOR}"
    if g.startswith(prefix):
        return g[len(prefix):]
    return g


def _is_gid(s: str) -> bool:
    """Check if a string is a gid."""
    return s.startswith(f"{env.GID_PREFIX}{env.GID_SEPARATOR}")


def _in_key(g: gid_t) -> str:
    """Get Redis key for a group's include set."""
    return f"{g}{env.LOGID_SUBKEY_SEPARATOR}{env.GID_IN_SUF}"


def _out_key(g: gid_t) -> str:
    """Get Redis key for a group's exclude set."""
    return f"{g}{env.LOGID_SUBKEY_SEPARATOR}{env.GID_OUT_SUF}"


# Modify membership


def add_include(name: str, member: logid_t | gid_t) -> bool:
    """Add a logid or gid to a group's include set.

    Returns:
        True if added, False if already present.
    """
    return env.r.sadd(_in_key(gid(name)), member) == 1


def add_exclude(name: str, member: logid_t | gid_t) -> bool:
    """Add a logid or gid to a group's exclude set.

    Returns:
        True if added, False if already present.
    """
    return env.r.sadd(_out_key(gid(name)), member) == 1


def remove_include(name: str, member: logid_t | gid_t) -> bool:
    """Remove a logid or gid from a group's include set.

    Returns:
        True if removed, False if not present.
    """
    return env.r.srem(_in_key(gid(name)), member) == 1


def remove_exclude(name: str, member: logid_t | gid_t) -> bool:
    """Remove a logid or gid from a group's exclude set.

    Returns:
        True if removed, False if not present.
    """
    return env.r.srem(_out_key(gid(name)), member) == 1


def get_include(name: str) -> set[logid_t | gid_t]:
    """Get the raw include set for a group."""
    return env.r.smembers(_in_key(gid(name)))


def get_exclude(name: str) -> set[logid_t | gid_t]:
    """Get the raw exclude set for a group."""
    return env.r.smembers(_out_key(gid(name)))


def delete(name: str) -> int:
    """Delete a group's include and exclude sets.

    Returns:
        Number of keys deleted (0, 1, or 2).
    """
    return env.r.delete(_in_key(gid(name)), _out_key(gid(name)))


# Query


def get_members(name: str) -> set[logid_t]:
    """Get all resolved members of a group.

    Resolves membership by:
    1. Collecting included members (direct + from included groups)
    2. Collecting excluded members (direct + from excluded groups)
    3. Returning included - excluded (excludes always win)

    Returns:
        Set of member logids.
    """
    included, excluded = _resolve(name, visited=set())
    return included - excluded


def _resolve(name: str, visited: set[str]) -> tuple[set[logid_t], set[logid_t]]:
    """Recursively resolve members with cycle detection.

    Returns:
        Tuple of (included_members, excluded_members).
    """
    from src import log

    # Cycle detection
    if name in visited:
        log.warning(f"Circular reference detected for group: {name}")
        return set(), set()

    visited = visited | {name}
    included: set[logid_t] = set()
    excluded: set[logid_t] = set()

    # Process includes
    for member in get_include(name):
        if _is_gid(member):
            group_name = _name(member)
            inc, exc = _resolve(group_name, visited)
            included |= inc
            excluded |= exc
        else:
            included.add(member)

    # Process excludes
    for member in get_exclude(name):
        if _is_gid(member):
            group_name = _name(member)
            exc_inc, exc_exc = _resolve(group_name, visited)
            excluded |= (exc_inc - exc_exc)
        else:
            excluded.add(member)

    return included, excluded


def is_member(member: logid_t, name: str) -> bool:
    """Check if a logid is a member of a group."""
    return member in get_members(name)
