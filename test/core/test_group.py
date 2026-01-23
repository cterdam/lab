import pytest

from src.core import group
from src.core.util import get_gid


def test_add_and_children_default_weight():
    """Test adding a member with default weight (INC=1)."""
    gid = get_gid("test_add_default")
    member = "member1"

    group.add(gid, member)
    result = group.children(gid)

    assert member in result
    assert result[member] == group.INC


def test_add_and_children_custom_weight():
    """Test adding a member with custom weight."""
    gid = get_gid("test_add_custom")
    member = "member1"
    weight = 0.5

    group.add(gid, member, weight)
    result = group.children(gid)

    assert member in result
    assert result[member] == weight


def test_add_updates_existing_member():
    """Test that adding an existing member updates its weight."""
    gid = get_gid("test_add_update")
    member = "member1"

    group.add(gid, member, 0.3)
    group.add(gid, member, 0.7)
    result = group.children(gid)

    assert result[member] == 0.7


def test_add_negative_weight():
    """Test adding a member with negative weight (exclusion)."""
    gid = get_gid("test_add_negative")
    member = "member1"

    group.add(gid, member, group.EXC)
    result = group.children(gid)

    assert result[member] == group.EXC


def test_rm_existing_member():
    """Test removing an existing member."""
    gid = get_gid("test_rm_existing")
    member = "member1"

    group.add(gid, member)
    result = group.rm(gid, member)

    assert result is True
    assert member not in group.children(gid)


def test_rm_nonexistent_member():
    """Test removing a member that doesn't exist."""
    gid = get_gid("test_rm_nonexistent")

    result = group.rm(gid, "nonexistent_member")

    assert result is False


def test_children_empty_group():
    """Test getting children of an empty group."""
    gid = get_gid("test_children_empty")

    result = group.children(gid)

    assert result == {}


def test_children_multiple_members():
    """Test getting children when group has multiple members."""
    gid = get_gid("test_children_multiple")

    group.add(gid, "m1", 1.0)
    group.add(gid, "m2", 0.5)
    group.add(gid, "m3", -0.5)

    result = group.children(gid)

    assert len(result) == 3
    assert result["m1"] == 1.0
    assert result["m2"] == 0.5
    assert result["m3"] == -0.5


def test_descendants_flat_group():
    """Test descendants with no nested groups."""
    gid = get_gid("test_desc_flat")

    group.add(gid, "m1", 1.0)
    group.add(gid, "m2", 0.5)

    result = group.descendants(gid)

    assert result["m1"] == 1.0
    assert result["m2"] == 0.5


def test_descendants_nested_groups():
    """Test descendants with nested groups."""
    parent = get_gid("test_desc_parent")
    child = get_gid("test_desc_child")

    group.add(child, "m1", 1.0)
    group.add(parent, child, 1.0)

    result = group.descendants(parent)

    assert child in result
    assert result[child] == 1.0
    assert "m1" in result
    assert result["m1"] == 1.0  # 1.0 * 1.0


def test_descendants_weight_multiplication():
    """Test that nested weights are multiplied."""
    parent = get_gid("test_desc_weight_mult_parent")
    child = get_gid("test_desc_weight_mult_child")

    group.add(child, "m1", 0.8)
    group.add(parent, child, 0.5)

    result = group.descendants(parent)

    assert result["m1"] == 0.4  # 0.5 * 0.8


def test_descendants_direct_overrides_indirect():
    """Test that direct membership overrides indirect."""
    parent = get_gid("test_desc_override_parent")
    child = get_gid("test_desc_override_child")

    group.add(child, "m1", 1.0)
    group.add(parent, child, 1.0)
    group.add(parent, "m1", -1.0)  # direct ban

    result = group.descendants(parent)

    assert result["m1"] == -1.0  # direct ban overrides indirect include


def test_descendants_only_positive_propagates():
    """Test that only positive scores propagate through nested groups."""
    parent = get_gid("test_desc_pos_prop_parent")
    child = get_gid("test_desc_pos_prop_child")

    group.add(child, "m1", -1.0)  # banned in child
    group.add(parent, child, 1.0)

    result = group.descendants(parent)

    # m1 should not propagate because its score in child is negative
    assert "m1" not in result or result.get("m1", 0) <= 0


def test_descendants_cycle_detection():
    """Test that cycles in group hierarchy don't cause infinite loops."""
    g1 = get_gid("test_desc_cycle_1")
    g2 = get_gid("test_desc_cycle_2")

    group.add(g1, g2, 1.0)
    group.add(g2, g1, 1.0)  # cycle
    group.add(g1, "m1", 1.0)

    # Should not hang
    result = group.descendants(g1)

    assert "m1" in result


def test_descendants_multiple_paths():
    """Test member reachable through multiple paths."""
    parent = get_gid("test_desc_multi_path_parent")
    child1 = get_gid("test_desc_multi_path_child1")
    child2 = get_gid("test_desc_multi_path_child2")

    group.add(child1, "m1", 1.0)
    group.add(child2, "m1", 1.0)
    group.add(parent, child1, 0.5)
    group.add(parent, child2, 0.3)

    result = group.descendants(parent)

    # Indirect score should be sum: 0.5*1.0 + 0.3*1.0 = 0.8
    # But there's no direct membership, so indirect applies
    assert result["m1"] == 0.8


def test_descendants_direct_overrides_multiple_indirect():
    """Test direct membership overrides even when multiple indirect paths exist."""
    parent = get_gid("test_desc_direct_multi_parent")
    child1 = get_gid("test_desc_direct_multi_child1")
    child2 = get_gid("test_desc_direct_multi_child2")

    group.add(child1, "m1", 1.0)
    group.add(child2, "m1", 1.0)
    group.add(parent, child1, 0.5)
    group.add(parent, child2, 0.5)
    group.add(parent, "m1", -1.0)  # direct ban

    result = group.descendants(parent)

    assert result["m1"] == -1.0  # direct ban overrides


def test_descendants_deep_nesting():
    """Test deeply nested group hierarchy."""
    g1 = get_gid("test_desc_deep_1")
    g2 = get_gid("test_desc_deep_2")
    g3 = get_gid("test_desc_deep_3")

    group.add(g3, "m1", 1.0)
    group.add(g2, g3, 0.5)
    group.add(g1, g2, 0.5)

    result = group.descendants(g1)

    assert result["m1"] == 0.25  # 0.5 * 0.5 * 1.0
