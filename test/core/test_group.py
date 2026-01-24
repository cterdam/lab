import pytest

from src.core import group
from src.core.util import get_gid


def test_add_and_children_default_weight():
    """Adding a member uses INC=1 by default."""
    gid = get_gid("test_add_default")
    member = "member1"

    group.add(gid, member)
    result = group.children(gid)

    assert member in result
    assert result[member] == group.INC


def test_add_and_children_custom_weight():
    """Adding a member with custom weight."""
    gid = get_gid("test_add_custom")
    member = "member1"
    weight = 0.5

    group.add(gid, member, weight)
    result = group.children(gid)

    assert member in result
    assert result[member] == weight


def test_add_updates_existing_member():
    """Adding an existing member updates its weight."""
    gid = get_gid("test_add_update")
    member = "member1"

    group.add(gid, member, 0.3)
    group.add(gid, member, 0.7)
    result = group.children(gid)

    assert result[member] == 0.7


def test_add_negative_weight():
    """Adding a member with negative weight (exclusion)."""
    gid = get_gid("test_add_negative")
    member = "member1"

    group.add(gid, member, group.EXC)
    result = group.children(gid)

    assert result[member] == group.EXC


def test_add_weight_clamping_upper():
    """Weight values above 1 are clamped to 1."""
    gid = get_gid("test_clamp_upper")
    member = "member1"

    group.add(gid, member, 5.0)
    result = group.children(gid)

    assert result[member] == 1.0


def test_add_weight_clamping_lower():
    """Weight values below -1 are clamped to -1."""
    gid = get_gid("test_clamp_lower")
    member = "member1"

    group.add(gid, member, -10.0)
    result = group.children(gid)

    assert result[member] == -1.0


def test_add_weight_within_range_not_clamped():
    """Weight values within [-1, 1] are not modified."""
    gid = get_gid("test_no_clamp")
    member = "member1"

    group.add(gid, member, 0.7)
    result = group.children(gid)

    assert result[member] == 0.7


def test_add_empty_gid_raises():
    """Adding with empty gid raises AssertionError."""
    with pytest.raises(AssertionError):
        group.add("", "member1")


def test_add_invalid_gid_format_raises():
    """Adding with invalid gid format raises AssertionError."""
    invalid_gid = "not_a_valid_gid_format"

    with pytest.raises(AssertionError):
        group.add(invalid_gid, "member1")


def test_rm_invalid_gid_raises():
    """Removing with invalid gid raises AssertionError."""
    with pytest.raises(AssertionError):
        group.rm("invalid", "member1")


def test_children_invalid_gid_raises():
    """Getting children with invalid gid raises AssertionError."""
    with pytest.raises(AssertionError):
        group.children("invalid")


def test_descendants_invalid_gid_raises():
    """Getting descendants with invalid gid raises AssertionError."""
    with pytest.raises(AssertionError):
        group.descendants("invalid")


def test_rm_existing_member():
    """Removing an existing member returns True."""
    gid = get_gid("test_rm_existing")
    member = "member1"

    group.add(gid, member)
    result = group.rm(gid, member)

    assert result is True
    assert member not in group.children(gid)


def test_rm_nonexistent_member():
    """Removing a nonexistent member returns False."""
    gid = get_gid("test_rm_nonexistent")

    result = group.rm(gid, "nonexistent_member")

    assert result is False


def test_children_empty_group():
    """Empty group returns empty dict."""
    gid = get_gid("test_children_empty")

    result = group.children(gid)

    assert result == {}


def test_children_multiple_members():
    """Group with multiple members returns all with weights."""
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
    """Flat group without nesting."""
    gid = get_gid("test_desc_flat")

    group.add(gid, "m1", 1.0)
    group.add(gid, "m2", 0.5)

    result = group.descendants(gid)

    assert result["m1"] == 1.0
    assert result["m2"] == 0.5


def test_descendants_nested_groups():
    """Nested group resolution."""
    parent = get_gid("test_desc_parent")
    child = get_gid("test_desc_child")

    group.add(child, "m1", 1.0)
    group.add(parent, child, 1.0)

    result = group.descendants(parent)

    assert child in result
    assert result[child] == 1.0
    assert "m1" in result
    assert result["m1"] == 1.0


def test_descendants_weight_multiplication():
    """Nested weights are multiplied."""
    parent = get_gid("test_desc_weight_mult_parent")
    child = get_gid("test_desc_weight_mult_child")

    group.add(child, "m1", 0.8)
    group.add(parent, child, 0.5)

    result = group.descendants(parent)

    assert result["m1"] == 0.4  # 0.5 * 0.8


def test_descendants_direct_overrides_indirect():
    """Direct membership overrides indirect."""
    parent = get_gid("test_desc_override_parent")
    child = get_gid("test_desc_override_child")

    group.add(child, "m1", 1.0)
    group.add(parent, child, 1.0)
    group.add(parent, "m1", -1.0)  # direct ban

    result = group.descendants(parent)

    assert result["m1"] == -1.0


def test_descendants_only_positive_propagates():
    """Negative scores don't propagate through nested groups."""
    parent = get_gid("test_desc_pos_prop_parent")
    child = get_gid("test_desc_pos_prop_child")

    group.add(child, "m1", -1.0)  # banned in child
    group.add(parent, child, 1.0)

    result = group.descendants(parent)

    assert "m1" not in result or result.get("m1", 0) <= 0


def test_descendants_cycle_detection():
    """Cycles don't cause infinite loops."""
    g1 = get_gid("test_desc_cycle_1")
    g2 = get_gid("test_desc_cycle_2")

    group.add(g1, g2, 1.0)
    group.add(g2, g1, 1.0)  # cycle
    group.add(g1, "m1", 1.0)

    result = group.descendants(g1)

    assert "m1" in result


def test_descendants_multiple_paths():
    """Multiple paths sum their contributions."""
    parent = get_gid("test_desc_multi_path_parent")
    child1 = get_gid("test_desc_multi_path_child1")
    child2 = get_gid("test_desc_multi_path_child2")

    group.add(child1, "m1", 1.0)
    group.add(child2, "m1", 1.0)
    group.add(parent, child1, 0.5)
    group.add(parent, child2, 0.3)

    result = group.descendants(parent)

    # 0.5*1.0 + 0.3*1.0 = 0.8
    assert result["m1"] == 0.8


def test_descendants_direct_overrides_multiple_indirect():
    """Direct membership overrides even with multiple indirect paths."""
    parent = get_gid("test_desc_direct_multi_parent")
    child1 = get_gid("test_desc_direct_multi_child1")
    child2 = get_gid("test_desc_direct_multi_child2")

    group.add(child1, "m1", 1.0)
    group.add(child2, "m1", 1.0)
    group.add(parent, child1, 0.5)
    group.add(parent, child2, 0.5)
    group.add(parent, "m1", -1.0)  # direct ban

    result = group.descendants(parent)

    assert result["m1"] == -1.0


def test_descendants_deep_nesting():
    """Deep hierarchy with weight multiplication."""
    g1 = get_gid("test_desc_deep_1")
    g2 = get_gid("test_desc_deep_2")
    g3 = get_gid("test_desc_deep_3")

    group.add(g3, "m1", 1.0)
    group.add(g2, g3, 0.5)
    group.add(g1, g2, 0.5)

    result = group.descendants(g1)

    assert result["m1"] == 0.25  # 0.5 * 0.5 * 1.0


# COMPLEX MULTI-PATH TESTS #####################################################
#
# Key behavior: visited set is shared across siblings, so shared subgraphs are
# traversed only once (first path wins). ZSET iteration is by score ascending.


def test_diamond_inheritance():
    r"""
    Diamond pattern where C (0.4) is processed first, traverses D.

        A
       / \
    (0.6) (0.4)
     /     \
    B       C
     \     /
    (1.0) (1.0)
       \ /
        D
        |
      (1.0)
        |
       m1

    m1 = 0.4 * 1.0 * 1.0 = 0.4
    """
    a = get_gid("test_diamond_a")
    b = get_gid("test_diamond_b")
    c = get_gid("test_diamond_c")
    d = get_gid("test_diamond_d")

    group.add(d, "m1", 1.0)
    group.add(b, d, 1.0)
    group.add(c, d, 1.0)
    group.add(a, b, 0.6)
    group.add(a, c, 0.4)

    result = group.descendants(a)

    assert result["m1"] == 0.4


def test_diamond_with_one_path_blocked():
    r"""
    Diamond where C bans D, so D's descendants don't propagate through C.

        A
       / \
    (1.0) (1.0)
     /     \
    B       C
     \     /
    (1.0) (-1.0)
       \ /
        D
        |
      (1.0)
        |
       m1

    m1 = 1.0 * 1.0 * 1.0 = 1.0 (through B only)
    """
    a = get_gid("test_diamond_blocked_a")
    b = get_gid("test_diamond_blocked_b")
    c = get_gid("test_diamond_blocked_c")
    d = get_gid("test_diamond_blocked_d")

    group.add(d, "m1", 1.0)
    group.add(b, d, 1.0)
    group.add(c, d, -1.0)
    group.add(a, b, 1.0)
    group.add(a, c, 1.0)

    result = group.descendants(a)

    assert result["m1"] == 1.0


def test_diamond_with_negative_edge_to_parent():
    r"""
    Diamond where C (-0.5) is processed first, traverses D.

        A
       / \
    (1.0) (-0.5)
     /     \
    B       C
     \     /
    (1.0) (1.0)
       \ /
        D
        |
      (1.0)
        |
       m1

    m1 = -0.5 * 1.0 * 1.0 = -0.5
    """
    a = get_gid("test_diamond_neg_edge_a")
    b = get_gid("test_diamond_neg_edge_b")
    c = get_gid("test_diamond_neg_edge_c")
    d = get_gid("test_diamond_neg_edge_d")

    group.add(d, "m1", 1.0)
    group.add(b, d, 1.0)
    group.add(c, d, 1.0)
    group.add(a, b, 1.0)
    group.add(a, c, -0.5)

    result = group.descendants(a)

    assert result["m1"] == -0.5


def test_triple_diamond():
    r"""
    Three paths where D (0.2) is processed first, traverses E.

           A
         / | \
      (0.5)(0.3)(0.2)
       /   |   \
      B    C    D
       \   |   /
      (1) (1) (1)
         \ | /
           E
           |
         (1.0)
           |
          m1

    m1 = 0.2 * 1.0 * 1.0 = 0.2
    """
    a = get_gid("test_triple_diamond_a")
    b = get_gid("test_triple_diamond_b")
    c = get_gid("test_triple_diamond_c")
    d = get_gid("test_triple_diamond_d")
    e = get_gid("test_triple_diamond_e")

    group.add(e, "m1", 1.0)
    group.add(b, e, 1.0)
    group.add(c, e, 1.0)
    group.add(d, e, 1.0)
    group.add(a, b, 0.5)
    group.add(a, c, 0.3)
    group.add(a, d, 0.2)

    result = group.descendants(a)

    assert result["m1"] == 0.2


def test_double_diamond_stacked():
    r"""
    Two diamonds stacked. F (0.4) traverses G first, B (0.5) traverses D first.

           A
          / \
       (0.5)(0.5)
        /     \
       B       C
        \     /
       (1.0)(1.0)
          \ /
           D
          / \
       (0.6)(0.4)
        /     \
       E       F
        \     /
       (1.0)(1.0)
          \ /
           G
           |
         (1.0)
           |
          m1

    D's m1 = 0.4 * 1.0 * 1.0 = 0.4
    A's m1 = 0.5 * 1.0 * 0.4 = 0.2
    """
    a = get_gid("test_double_diamond_a")
    b = get_gid("test_double_diamond_b")
    c = get_gid("test_double_diamond_c")
    d = get_gid("test_double_diamond_d")
    e = get_gid("test_double_diamond_e")
    f = get_gid("test_double_diamond_f")
    g = get_gid("test_double_diamond_g")

    group.add(g, "m1", 1.0)
    group.add(e, g, 1.0)
    group.add(f, g, 1.0)
    group.add(d, e, 0.6)
    group.add(d, f, 0.4)
    group.add(b, d, 1.0)
    group.add(c, d, 1.0)
    group.add(a, b, 0.5)
    group.add(a, c, 0.5)

    result = group.descendants(a)

    assert result["m1"] == 0.2


def test_complex_mixed_include_exclude():
    """
    Multiple members with mixed include/exclude.

           A
         / | \
      (1) (1) (1)
       /   |   \
      B    C    D
      |    |    |
    m1:1 m1:-1 m2:1
    m2:1       m1:0.5

    m1: B=1, C doesn't propagate (negative), D=0.5. Total=1.5
    m2: B=1, D=1. Total=2.0
    """
    a = get_gid("test_complex_mixed_a")
    b = get_gid("test_complex_mixed_b")
    c = get_gid("test_complex_mixed_c")
    d = get_gid("test_complex_mixed_d")

    group.add(b, "m1", 1.0)
    group.add(b, "m2", 1.0)
    group.add(c, "m1", -1.0)
    group.add(d, "m2", 1.0)
    group.add(d, "m1", 0.5)
    group.add(a, b, 1.0)
    group.add(a, c, 1.0)
    group.add(a, d, 1.0)

    result = group.descendants(a)

    assert result["m1"] == 1.5
    assert result["m2"] == 2.0


def test_deep_chain_with_alternating_weights():
    """
    Deep chain: A->(0.8)->B->(0.5)->C->(0.9)->D->(0.4)->E->(1.0)->m1

    m1 = 0.8 * 0.5 * 0.9 * 0.4 * 1.0 = 0.144
    """
    a = get_gid("test_deep_chain_a")
    b = get_gid("test_deep_chain_b")
    c = get_gid("test_deep_chain_c")
    d = get_gid("test_deep_chain_d")
    e = get_gid("test_deep_chain_e")

    group.add(e, "m1", 1.0)
    group.add(d, e, 0.4)
    group.add(c, d, 0.9)
    group.add(b, c, 0.5)
    group.add(a, b, 0.8)

    result = group.descendants(a)

    expected = 0.8 * 0.5 * 0.9 * 0.4 * 1.0
    assert abs(result["m1"] - expected) < 1e-9


def test_parallel_chains_converging():
    """
    Two chains converging. C (0.3) processed first, traverses D.

    A --(0.7)--> B --(0.6)--> D --(1.0)--> m1
    A --(0.3)--> C --(0.8)--> D

    m1 = 0.3 * 0.8 * 1.0 = 0.24
    """
    a = get_gid("test_parallel_chains_a")
    b = get_gid("test_parallel_chains_b")
    c = get_gid("test_parallel_chains_c")
    d = get_gid("test_parallel_chains_d")

    group.add(d, "m1", 1.0)
    group.add(b, d, 0.6)
    group.add(c, d, 0.8)
    group.add(a, b, 0.7)
    group.add(a, c, 0.3)

    result = group.descendants(a)

    assert abs(result["m1"] - 0.24) < 1e-9


def test_lattice_structure():
    r"""
    Lattice where B processes E first, E traverses H.

           A
          /|\
       (1)(1)(1)
        / | \
       B  C  D
       |\/|\/|
       |/\|/\|
       E  F  G    (each with weight 0.5)
        \ | /
       (1)(1)(1)
          |
          H
          |
        (1.0)
          |
         m1

    m1 = 1.0 * 0.5 * 1.0 * 1.0 = 0.5
    """
    a = get_gid("test_lattice_a")
    b = get_gid("test_lattice_b")
    c = get_gid("test_lattice_c")
    d = get_gid("test_lattice_d")
    e = get_gid("test_lattice_e")
    f = get_gid("test_lattice_f")
    g = get_gid("test_lattice_g")
    h = get_gid("test_lattice_h")

    group.add(h, "m1", 1.0)
    group.add(e, h, 1.0)
    group.add(f, h, 1.0)
    group.add(g, h, 1.0)

    for parent in [b, c, d]:
        for child in [e, f, g]:
            group.add(parent, child, 0.5)

    group.add(a, b, 1.0)
    group.add(a, c, 1.0)
    group.add(a, d, 1.0)

    result = group.descendants(a)

    assert abs(result["m1"] - 0.5) < 1e-9


def test_exclude_at_intermediate_level():
    """
    Intermediate group excludes the member, blocking propagation.

    A --(1.0)--> B --(1.0)--> C (m1: -1.0)
    A --(1.0)--> D --(1.0)--> E (m1: 1.0)

    m1 = 1.0 * 1.0 * 1.0 = 1.0 (through E only)
    """
    a = get_gid("test_exclude_intermediate_a")
    b = get_gid("test_exclude_intermediate_b")
    c = get_gid("test_exclude_intermediate_c")
    d = get_gid("test_exclude_intermediate_d")
    e = get_gid("test_exclude_intermediate_e")

    group.add(c, "m1", -1.0)
    group.add(e, "m1", 1.0)
    group.add(b, c, 1.0)
    group.add(d, e, 1.0)
    group.add(a, b, 1.0)
    group.add(a, d, 1.0)

    result = group.descendants(a)

    assert result["m1"] == 1.0


def test_direct_override_deep_in_hierarchy():
    """
    Direct membership at intermediate level contributes alongside deeper paths.

           A
          / \
       (1.0)(1.0)
        /     \
       B       C
       |       |
     m1:0.1  (1.0)
               |
               D
               |
             m1:1.0

    m1 = 1.0*0.1 + 1.0*1.0*1.0 = 1.1
    """
    a = get_gid("test_direct_deep_a")
    b = get_gid("test_direct_deep_b")
    c = get_gid("test_direct_deep_c")
    d = get_gid("test_direct_deep_d")

    group.add(b, "m1", 0.1)
    group.add(d, "m1", 1.0)
    group.add(c, d, 1.0)
    group.add(a, b, 1.0)
    group.add(a, c, 1.0)

    result = group.descendants(a)

    assert abs(result["m1"] - 1.1) < 1e-9


def test_cycle_in_diamond():
    r"""
    Diamond with a cycle between B and C. Should not hang.

        A
       / \
    (1.0)(1.0)
     /     \
    B <---> C
     \     /
    (1.0)(1.0)
       \ /
        D
        |
      (1.0)
        |
       m1
    """
    a = get_gid("test_cycle_diamond_a")
    b = get_gid("test_cycle_diamond_b")
    c = get_gid("test_cycle_diamond_c")
    d = get_gid("test_cycle_diamond_d")

    group.add(d, "m1", 1.0)
    group.add(b, d, 1.0)
    group.add(c, d, 1.0)
    group.add(b, c, 1.0)
    group.add(c, b, 1.0)
    group.add(a, b, 1.0)
    group.add(a, c, 1.0)

    result = group.descendants(a)

    assert "m1" in result
    assert result["m1"] > 0
