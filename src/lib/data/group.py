"""Redis-backed group membership management.

Groups are identified by gid (group ID) in format: g:groupname
- The prefix "g" and separator ":" are configurable in env.

Redis keys:
- gids: SET of all gids
- {gid}/include: SET of included logids (groups or members)
- {gid}/exclude: SET of excluded logids (groups or members)

Resolution: included - excluded, with recursive expansion for nested groups.
"""

from src import env
from src.core import gid_t, logid_t


def _gid(name: str) -> gid_t:
    """Convert a group name to a gid."""
    return f"{env.GID_PREFIX}{env.GID_SEPARATOR}{name}"


def _name(gid: gid_t) -> str:
    """Extract group name from a gid."""
    prefix = f"{env.GID_PREFIX}{env.GID_SEPARATOR}"
    if gid.startswith(prefix):
        return gid[len(prefix):]
    return gid


def _is_gid(s: str) -> bool:
    """Check if a string is a gid."""
    return s.startswith(f"{env.GID_PREFIX}{env.GID_SEPARATOR}")


def _include_key(gid: gid_t) -> str:
    """Get Redis key for a group's include set."""
    return f"{gid}{env.LOGID_SUBKEY_SEPARATOR}include"


def _exclude_key(gid: gid_t) -> str:
    """Get Redis key for a group's exclude set."""
    return f"{gid}{env.LOGID_SUBKEY_SEPARATOR}exclude"


# Group management


def create(name: str) -> gid_t | None:
    """Create a new group.

    Returns:
        The gid if created, None if already exists.
    """
    gid = _gid(name)
    if env.r.sadd(env.GIDS_KEY, gid) == 1:
        return gid
    return None


def delete(name: str) -> bool:
    """Delete a group and its include/exclude sets.

    Returns:
        True if deleted, False if not found.
    """
    gid = _gid(name)
    if not env.r.sismember(env.GIDS_KEY, gid):
        return False
    env.r.srem(env.GIDS_KEY, gid)
    env.r.delete(_include_key(gid), _exclude_key(gid))
    return True


def exists(name: str) -> bool:
    """Check if a group exists."""
    return env.r.sismember(env.GIDS_KEY, _gid(name))


def list_all() -> set[gid_t]:
    """List all gids."""
    return env.r.smembers(env.GIDS_KEY)


# Modify membership


def add_include(name: str, member: logid_t | gid_t) -> bool:
    """Add a logid or gid to a group's include set.

    Returns:
        True if added, False if already present or group doesn't exist.
    """
    if not exists(name):
        return False
    return env.r.sadd(_include_key(_gid(name)), member) == 1


def add_exclude(name: str, member: logid_t | gid_t) -> bool:
    """Add a logid or gid to a group's exclude set.

    Returns:
        True if added, False if already present or group doesn't exist.
    """
    if not exists(name):
        return False
    return env.r.sadd(_exclude_key(_gid(name)), member) == 1


def remove_include(name: str, member: logid_t | gid_t) -> bool:
    """Remove a logid or gid from a group's include set.

    Returns:
        True if removed, False if not present or group doesn't exist.
    """
    if not exists(name):
        return False
    return env.r.srem(_include_key(_gid(name)), member) == 1


def remove_exclude(name: str, member: logid_t | gid_t) -> bool:
    """Remove a logid or gid from a group's exclude set.

    Returns:
        True if removed, False if not present or group doesn't exist.
    """
    if not exists(name):
        return False
    return env.r.srem(_exclude_key(_gid(name)), member) == 1


def get_include(name: str) -> set[logid_t | gid_t]:
    """Get the raw include set for a group."""
    return env.r.smembers(_include_key(_gid(name)))


def get_exclude(name: str) -> set[logid_t | gid_t]:
    """Get the raw exclude set for a group."""
    return env.r.smembers(_exclude_key(_gid(name)))


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
    for member in get_include(name):
        if _is_gid(member):
            group_name = _name(member)
            if exists(group_name):
                inc, exc = _resolve(group_name, visited)
                included |= inc
                excluded |= exc
                continue
        # It's an individual member
        included.add(member)

    # Process excludes
    for member in get_exclude(name):
        if _is_gid(member):
            group_name = _name(member)
            if exists(group_name):
                exc_inc, exc_exc = _resolve(group_name, visited)
                excluded |= (exc_inc - exc_exc)
                continue
        excluded.add(member)

    return included, excluded


def is_member(member: logid_t, name: str) -> bool:
    """Check if a logid is a member of a group."""
    return member in get_members(name)


def get_groups(member: logid_t) -> set[gid_t]:
    """Get all groups that contain a logid as a member."""
    result = set()
    for gid in list_all():
        name = _name(gid)
        if is_member(member, name):
            result.add(gid)
    return result


def gid(name: str) -> gid_t:
    """Get the gid for a group name."""
    return _gid(name)
