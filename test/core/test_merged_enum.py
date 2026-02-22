from enum import Enum, IntEnum, StrEnum

import pytest

from src.core.util import MergedEnum

# BASIC FUNCTIONALITY ##########################################################


def test_single_class():
    """MergedEnum on a class with its own _gona."""

    class Base:
        gona = MergedEnum("_gona", StrEnum)

        class _gona(StrEnum):
            A = "a"

    assert list(Base.gona) == [Base.gona.A]
    assert Base.gona.A == "a"


def test_inheritance():
    """Child merges parent's members with its own."""

    class Base:
        gona = MergedEnum("_gona", StrEnum)

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
        gona = MergedEnum("_gona", StrEnum)

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


# ENUM TYPE PARAMETER #########################################################


def test_default_enum_type():
    """Default enum_type is plain Enum."""

    class Base:
        gona = MergedEnum("_gona")

        class _gona(Enum):
            A = "a"

    assert Base.gona.A.value == "a"
    assert not isinstance(Base.gona.A, str)


def test_strenum_type():
    """StrEnum makes members usable as strings directly."""

    class Base:
        gona = MergedEnum("_gona", StrEnum)

        class _gona(StrEnum):
            A = "a"

    class Child(Base):
        class _gona(StrEnum):
            B = "b"

    assert isinstance(Child.gona.A, str)
    assert Child.gona.A == "a"
    assert Child.gona.B == "b"


def test_intenum_type():
    """IntEnum makes members usable as ints directly."""

    class Base:
        vals = MergedEnum("_vals", IntEnum)

        class _vals(IntEnum):
            X = 1

    class Child(Base):
        class _vals(IntEnum):
            Y = 2

    assert isinstance(Child.vals.X, int)
    assert Child.vals.X == 1
    assert Child.vals.Y == 2


# INSTANCE ACCESS ##############################################################


def test_instance_access():
    """Descriptor works on instances too."""

    class Base:
        gona = MergedEnum("_gona", StrEnum)

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


def test_duplicate_key_raises():
    """Duplicate key across hierarchy raises ValueError."""

    class Base:
        gona = MergedEnum("_gona", StrEnum)

        class _gona(StrEnum):
            A = "a1"

    class Child(Base):
        class _gona(StrEnum):
            A = "a2"

    with pytest.raises(ValueError, match="Duplicate.*key"):
        Child.gona


def test_duplicate_value_raises():
    """Duplicate value across hierarchy raises ValueError."""

    class Base:
        gona = MergedEnum("_gona", StrEnum)

        class _gona(StrEnum):
            A = "shared"

    class Child(Base):
        class _gona(StrEnum):
            B = "shared"

    with pytest.raises(ValueError, match="duplicate values found"):
        Child.gona


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


# MULTIPLE DESCRIPTORS ########################################################


def test_multiple_descriptors_on_same_class():
    """Multiple MergedEnum descriptors on the same base are independent."""

    class Base:
        coke = MergedEnum("_coke", StrEnum)
        logmsg = MergedEnum("_logmsg", StrEnum)

        class _coke(StrEnum):
            INVOC = "invoc"

        class _logmsg(StrEnum):
            MSG = "hello"

    assert set(Base.coke.__members__) == {"INVOC"}
    assert set(Base.logmsg.__members__) == {"MSG"}
    assert Base.coke.INVOC == "invoc"
    assert Base.logmsg.MSG == "hello"


def test_multiple_descriptors_merge_independently():
    """Each descriptor merges only its own part_attr across the MRO."""

    class Base:
        coke = MergedEnum("_coke", StrEnum)
        logmsg = MergedEnum("_logmsg", StrEnum)

        class _coke(StrEnum):
            A = "a"

        class _logmsg(StrEnum):
            X = "x"

    class Child(Base):
        class _coke(StrEnum):
            B = "b"

    # coke merges, logmsg inherits unchanged
    assert set(Child.coke.__members__) == {"A", "B"}
    assert set(Child.logmsg.__members__) == {"X"}

    # Base is unaffected
    assert set(Base.coke.__members__) == {"A"}


def test_descriptor_none_when_other_exists():
    """A descriptor with no parts returns None even if sibling has parts."""

    class Base:
        coke = MergedEnum("_coke", StrEnum)
        logmsg = MergedEnum("_logmsg", StrEnum)

        class _coke(StrEnum):
            A = "a"

    assert Base.coke.A == "a"
    assert Base.logmsg is None


def test_duplicate_across_descriptors_allowed():
    """Same member name in different descriptors is fine."""

    class Base:
        coke = MergedEnum("_coke", StrEnum)
        logmsg = MergedEnum("_logmsg", StrEnum)

        class _coke(StrEnum):
            NAME = "counter"

        class _logmsg(StrEnum):
            NAME = "message"

    assert Base.coke.NAME == "counter"
    assert Base.logmsg.NAME == "message"


# REAL HIERARCHY PATTERNS #####################################################


def test_logger_algo_pattern():
    """Simulates Logger -> Algo hierarchy with coke and logmsg."""

    class Logger:
        coke = MergedEnum("_coke", StrEnum)
        logmsg = MergedEnum("_logmsg", StrEnum)

        class _logmsg(StrEnum):
            FUNC_INPUT = "func_input"
            FUNC_OUTPUT = "func_output"

    class Algo(Logger):
        class _coke(StrEnum):
            INVOC = "invoc"
            MICROS = "micros"

    # Algo gets its own coke and inherits Logger's logmsg
    assert set(Algo.coke.__members__) == {"INVOC", "MICROS"}
    assert Algo.coke.INVOC == "invoc"
    assert set(Algo.logmsg.__members__) == {"FUNC_INPUT", "FUNC_OUTPUT"}

    # Logger has no coke of its own
    assert Logger.coke is None
    assert set(Logger.logmsg.__members__) == {"FUNC_INPUT", "FUNC_OUTPUT"}


def test_logger_grouplogger_pattern():
    """Simulates Logger -> _GroupLogger with logmsg merging."""

    class Logger:
        logmsg = MergedEnum("_logmsg", StrEnum)

        class _logmsg(StrEnum):
            FUNC_INPUT = "func_input"
            COUNT_SET = "count_set"

    class GroupLogger(Logger):
        class _logmsg(StrEnum):
            ADD = "add"
            RM = "rm"

    # GroupLogger merges both sets
    assert set(GroupLogger.logmsg.__members__) == {
        "FUNC_INPUT",
        "COUNT_SET",
        "ADD",
        "RM",
    }
    assert GroupLogger.logmsg.ADD == "add"
    assert GroupLogger.logmsg.FUNC_INPUT == "func_input"

    # Logger unaffected
    assert set(Logger.logmsg.__members__) == {"FUNC_INPUT", "COUNT_SET"}
