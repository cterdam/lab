"""Redis-backed group membership management.

Groups are stored as Redis sets. Each group has:
- group:{name}/include - SET of included logids (groups or members)
- group:{name}/exclude - SET of excluded logids (groups or members)

All groups are tracked in the 'groups' SET.

Resolution: included - excluded, with recursive expansion for nested groups.
"""

from src import env
from src.core import logid_t

# Redis key constants
GROUPS_KEY = "groups"
GROUP_PREFIX = "group"


def _include_key(name: str) -> str:
    """Get Redis key for a group's include set."""
    return f"{GROUP_PREFIX}:{name}{env.LOGID_SUBKEY_SEPARATOR}include"


def _exclude_key(name: str) -> str:
    """Get Redis key for a group's exclude set."""
    return f"{GROUP_PREFIX}:{name}{env.LOGID_SUBKEY_SEPARATOR}exclude"


# Group management


def create(name: str) -> bool:
    """Create a new group.

    Returns:
        True if created, False if already exists.
    """
    return env.r.sadd(GROUPS_KEY, name) == 1


def delete(name: str) -> bool:
    """Delete a group and its include/exclude sets.

    Returns:
        True if deleted, False if not found.
    """
    if not env.r.sismember(GROUPS_KEY, name):
        return False
    env.r.srem(GROUPS_KEY, name)
    env.r.delete(_include_key(name), _exclude_key(name))
    return True


def exists(name: str) -> bool:
    """Check if a group exists."""
    return env.r.sismember(GROUPS_KEY, name)


def list_all() -> set[str]:
    """List all group names."""
    return env.r.smembers(GROUPS_KEY)


# Modify membership


def add_include(name: str, logid: logid_t) -> bool:
    """Add a logid to a group's include set.

    Returns:
        True if added, False if already present or group doesn't exist.
    """
    if not exists(name):
        return False
    return env.r.sadd(_include_key(name), logid) == 1


def add_exclude(name: str, logid: logid_t) -> bool:
    """Add a logid to a group's exclude set.

    Returns:
        True if added, False if already present or group doesn't exist.
    """
    if not exists(name):
        return False
    return env.r.sadd(_exclude_key(name), logid) == 1


def remove_include(name: str, logid: logid_t) -> bool:
    """Remove a logid from a group's include set.

    Returns:
        True if removed, False if not present or group doesn't exist.
    """
    if not exists(name):
        return False
    return env.r.srem(_include_key(name), logid) == 1


def remove_exclude(name: str, logid: logid_t) -> bool:
    """Remove a logid from a group's exclude set.

    Returns:
        True if removed, False if not present or group doesn't exist.
    """
    if not exists(name):
        return False
    return env.r.srem(_exclude_key(name), logid) == 1


def get_include(name: str) -> set[logid_t]:
    """Get the raw include set for a group."""
    return env.r.smembers(_include_key(name))


def get_exclude(name: str) -> set[logid_t]:
    """Get the raw exclude set for a group."""
    return env.r.smembers(_exclude_key(name))


# Query


def get_members(name: str) -> set[logid_t]:
    """Get all resolved members of a group.

    Resolves membership by:
    1. Collecting included members (direct + from included groups)
    2. Collecting excluded members (direct + from excluded groups)
    3. Returning included - excluded (excludes always win)

    Returns:
        Set of member logids, empty if group not found or cycle detected.
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

    # Group not found
    if not exists(name):
        log.warning(f"Group not found: {name}")
        return set(), set()

    visited = visited | {name}
    included: set[logid_t] = set()
    excluded: set[logid_t] = set()

    # Process includes
    for logid in get_include(name):
        # Check if it's a group (extract name from group:NAME format)
        if logid.startswith(f"{GROUP_PREFIX}:"):
            group_name = logid[len(f"{GROUP_PREFIX}:"):]
            if exists(group_name):
                inc, exc = _resolve(group_name, visited)
                included |= inc
                excluded |= exc
                continue
        # It's an individual member
        included.add(logid)

    # Process excludes
    for logid in get_exclude(name):
        if logid.startswith(f"{GROUP_PREFIX}:"):
            group_name = logid[len(f"{GROUP_PREFIX}:"):]
            if exists(group_name):
                exc_inc, exc_exc = _resolve(group_name, visited)
                excluded |= (exc_inc - exc_exc)
                continue
        excluded.add(logid)

    return included, excluded


def is_member(logid: logid_t, name: str) -> bool:
    """Check if a logid is a member of a group."""
    return logid in get_members(name)


def get_groups(logid: logid_t) -> set[str]:
    """Get all groups that contain a logid as a member."""
    result = set()
    for name in list_all():
        if is_member(logid, name):
            result.add(name)
    return result


def logid(name: str) -> logid_t:
    """Get the logid for a group name."""
    return f"{GROUP_PREFIX}:{name}"
