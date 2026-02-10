from enum import Enum, IntEnum, StrEnum

import pytest

from src.core.util import MergedEnum


# BASIC FUNCTIONALITY ##########################################################


def test_single_class():
    """MergedEnum on a class with its own _gona."""

    class Base:
        gona = MergedEnum("_gona")

        class _gona(StrEnum):
            A = "a"

    assert list(Base.gona) == [Base.gona.A]
    assert Base.gona.A == "a"


def test_inheritance():
    """Child merges parent's members with its own."""

    class Base:
        gona = MergedEnum("_gona")

        class _gona(StrEnum):
            A = "a"

    class Child(Base):
        class _gona(StrEnum):
            B = "b"

    assert "A" in Base.gona.__members__
    assert "B" not in Base.gona.__members__
    assert "A" in Child.gona.__members__
    assert "B" in Child.gona.__members__
    assert Child.gona.A == "a"
    assert Child.gona.B == "b"


def test_deep_hierarchy():
    """Members accumulate across multiple levels."""

    class L0:
        gona = MergedEnum("_gona")

        class _gona(StrEnum):
            A = "a"

    class L1(L0):
        class _gona(StrEnum):
            B = "b"

    class L2(L1):
        class _gona(StrEnum):
            C = "c"

    assert set(L2.gona.__members__) == {"A", "B", "C"}
    assert set(L1.gona.__members__) == {"A", "B"}
    assert set(L0.gona.__members__) == {"A"}


def test_child_without_own_part():
    """Child with no _gona inherits parent's merged enum."""

    class Base:
        gona = MergedEnum("_gona")

        class _gona(StrEnum):
            A = "a"

    class Child(Base):
        pass

    assert set(Child.gona.__members__) == {"A"}
    assert Child.gona.A == "a"


# MULTIPLE INHERITANCE #########################################################


def test_diamond():
    """Multiple inheritance merges from all branches."""

    class Base:
        gona = MergedEnum("_gona")

        class _gona(StrEnum):
            A = "a"

    class Left(Base):
        class _gona(StrEnum):
            B = "b"

    class Right(Base):
        class _gona(StrEnum):
            C = "c"

    class Diamond(Left, Right):
        pass

    assert set(Diamond.gona.__members__) == {"A", "B", "C"}


def test_diamond_with_own_members():
    """Diamond class adds its own members too."""

    class Base:
        gona = MergedEnum("_gona")

        class _gona(StrEnum):
            A = "a"

    class Left(Base):
        class _gona(StrEnum):
            B = "b"

    class Right(Base):
        class _gona(StrEnum):
            C = "c"

    class Diamond(Left, Right):
        class _gona(StrEnum):
            D = "d"

    assert set(Diamond.gona.__members__) == {"A", "B", "C", "D"}


def test_multiple_inheritance_no_overlap():
    """Sibling classes have independent merged enums."""

    class Base:
        gona = MergedEnum("_gona")

        class _gona(StrEnum):
            A = "a"

    class Left(Base):
        class _gona(StrEnum):
            B = "b"

    class Right(Base):
        class _gona(StrEnum):
            C = "c"

    assert set(Left.gona.__members__) == {"A", "B"}
    assert set(Right.gona.__members__) == {"A", "C"}


# ENUM TYPE PRESERVATION #######################################################


def test_strenum_type():
    """Merged enum preserves StrEnum type."""

    class Base:
        gona = MergedEnum("_gona")

        class _gona(StrEnum):
            A = "a"

    class Child(Base):
        class _gona(StrEnum):
            B = "b"

    assert isinstance(Child.gona.A, str)
    assert isinstance(Child.gona.B, str)


def test_intenum_type():
    """Merged enum preserves IntEnum type."""

    class Base:
        vals = MergedEnum("_vals")

        class _vals(IntEnum):
            X = 1

    class Child(Base):
        class _vals(IntEnum):
            Y = 2

    assert isinstance(Child.vals.X, int)
    assert isinstance(Child.vals.Y, int)
    assert Child.vals.X == 1
    assert Child.vals.Y == 2


def test_plain_enum_type():
    """Works with plain Enum."""

    class Base:
        kinds = MergedEnum("_kinds")

        class _kinds(Enum):
            FOO = "foo"

    class Child(Base):
        class _kinds(Enum):
            BAR = "bar"

    assert set(Child.kinds.__members__) == {"FOO", "BAR"}


# INSTANCE ACCESS ##############################################################


def test_instance_access():
    """Descriptor works on instances too."""

    class Base:
        gona = MergedEnum("_gona")

        class _gona(StrEnum):
            A = "a"

    class Child(Base):
        class _gona(StrEnum):
            B = "b"

    obj = Child()
    assert set(obj.gona.__members__) == {"A", "B"}
    assert obj.gona.A == "a"


# CACHING ######################################################################


def test_caching():
    """Same object returned on repeated access."""

    class Base:
        gona = MergedEnum("_gona")

        class _gona(StrEnum):
            A = "a"

    assert Base.gona is Base.gona


def test_per_class_caching():
    """Different classes get different cached enums."""

    class Base:
        gona = MergedEnum("_gona")

        class _gona(StrEnum):
            A = "a"

    class Child(Base):
        class _gona(StrEnum):
            B = "b"

    assert Base.gona is not Child.gona


# EDGE CASES ###################################################################


def test_no_parts():
    """Returns None if no _gona defined anywhere."""

    class Base:
        gona = MergedEnum("_gona")

    assert Base.gona is None


def test_override_value():
    """Later class in MRO overrides a member's value."""

    class Base:
        gona = MergedEnum("_gona")

        class _gona(StrEnum):
            A = "a1"

    class Child(Base):
        class _gona(StrEnum):
            A = "a2"

    assert Child.gona.A == "a2"
    assert Base.gona.A == "a1"


def test_iteration():
    """Merged enum is iterable."""

    class Base:
        gona = MergedEnum("_gona")

        class _gona(StrEnum):
            A = "a"
            B = "b"

    class Child(Base):
        class _gona(StrEnum):
            C = "c"

    names = [m.name for m in Child.gona]
    assert set(names) == {"A", "B", "C"}
