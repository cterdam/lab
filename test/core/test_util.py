import re

import pytest

from src.core.util import (
    as_filename,
    descendant_classes,
    get_gid,
    is_gid,
    is_logid,
    randalnu,
)
from src.lib.game.event import Event, GameEnd, GameStart, Interrupt, Speech


def test_as_filename_basic():
    assert as_filename("openai/gpt-4.1") == "openai_gpt-4_1"


def test_as_filename_emojis_symbols():
    assert (
        as_filename("mistral‑ai/mixtral‑8x7b‑inst/💡") == "mistral_ai_mixtral_8x7b_inst"
    )


def test_as_filename_strips_extra_underscores():
    assert as_filename("///hello///") == "hello"


def test_as_filename_consecutive_special_chars():
    assert as_filename("hello!!world") == "hello_world"


def test_as_filename_invalid():
    with pytest.raises(ValueError):
        as_filename("💡💡💡")


def test_randalnu_default_length():
    result = randalnu()
    assert isinstance(result, str)
    assert len(result) == 4
    assert re.match(r"^[a-z0-9]{4}$", result)


def test_randalnu_custom_length():
    for length in [1, 6, 10]:
        result = randalnu(length)
        assert len(result) == length
        assert re.match(r"^[a-z0-9]+$", result)


def test_randalnu_randomness():
    num_trials = 100
    samples = {randalnu() for _ in range(num_trials)}
    assert len(samples) == num_trials


def test_descendant_classes_no_subclasses():
    """Test that a class with no subclasses returns empty dict."""

    class Base:
        pass

    result = descendant_classes(Base)
    assert result == {}


def test_descendant_classes_single_level():
    """Test finding direct subclasses only."""

    class Base:
        pass

    class Sub1(Base):
        pass

    class Sub2(Base):
        pass

    result = descendant_classes(Base)
    assert len(result) == 2
    assert result["Sub1"] == Sub1
    assert result["Sub2"] == Sub2
    assert "Base" not in result


def test_descendant_classes_nested():
    """Test finding subclasses at multiple levels."""

    class Base:
        pass

    class Sub1(Base):
        pass

    class Sub2(Base):
        pass

    class SubSub1(Sub1):
        pass

    class SubSub2(Sub1):
        pass

    class DeepSub(SubSub1):
        pass

    result = descendant_classes(Base)
    assert len(result) == 5
    assert result["Sub1"] == Sub1
    assert result["Sub2"] == Sub2
    assert result["SubSub1"] == SubSub1
    assert result["SubSub2"] == SubSub2
    assert result["DeepSub"] == DeepSub
    assert "Base" not in result


def test_descendant_classes_multiple_branches():
    """Test finding subclasses across multiple inheritance branches."""

    class Base:
        pass

    class Branch1(Base):
        pass

    class Branch2(Base):
        pass

    class Branch1Leaf1(Branch1):
        pass

    class Branch1Leaf2(Branch1):
        pass

    class Branch2Leaf(Branch2):
        pass

    result = descendant_classes(Base)
    assert len(result) == 5
    assert result["Branch1"] == Branch1
    assert result["Branch2"] == Branch2
    assert result["Branch1Leaf1"] == Branch1Leaf1
    assert result["Branch1Leaf2"] == Branch1Leaf2
    assert result["Branch2Leaf"] == Branch2Leaf


def test_descendant_classes_very_deep():
    """Test finding subclasses in a very deep hierarchy."""

    class Level0:
        pass

    class Level1(Level0):
        pass

    class Level2(Level1):
        pass

    class Level3(Level2):
        pass

    class Level4(Level3):
        pass

    result = descendant_classes(Level0)
    assert len(result) == 4
    assert result["Level1"] == Level1
    assert result["Level2"] == Level2
    assert result["Level3"] == Level3
    assert result["Level4"] == Level4


def test_descendant_classes_with_game_event():
    """Test with actual GameEvent hierarchy to ensure it works in practice."""

    result = descendant_classes(Event)

    # Should find all event subclasses
    assert "GameStart" in result
    assert "GameEnd" in result
    assert "Speech" in result
    assert "Interrupt" in result

    # Verify the mappings are correct
    assert result["GameStart"] == GameStart
    assert result["GameEnd"] == GameEnd
    assert result["Speech"] == Speech
    assert result["Interrupt"] == Interrupt

    # Should not include GameEvent itself
    assert "GameEvent" not in result


def test_is_gid_valid():
    """Test is_gid with valid group IDs."""
    gid = get_gid("mygroup")
    assert is_gid(gid) is True


def test_is_gid_invalid_format():
    """Test is_gid with invalid format."""
    assert is_gid("not_a_gid") is False
    assert is_gid("wrong:namespace") is False


def test_is_gid_empty():
    """Test is_gid with empty string."""
    assert is_gid("") is False


def test_is_gid_non_string():
    """Test is_gid with non-string types."""
    assert is_gid(None) is False
    assert is_gid(123) is False
    assert is_gid([]) is False


def test_is_logid_valid():
    """Test is_logid with valid object IDs."""
    assert is_logid("namespace:name") is True
    assert is_logid("g:group1") is True
    assert is_logid("logger:main") is True


def test_is_logid_invalid_no_separator():
    """Test is_logid with no separator."""
    assert is_logid("noseparator") is False


def test_is_logid_empty():
    """Test is_logid with empty string."""
    assert is_logid("") is False


def test_is_logid_non_string():
    """Test is_logid with non-string types."""
    assert is_logid(None) is False
    assert is_logid(123) is False
    assert is_logid({}) is False


def test_is_logid_gid_is_logid():
    """Test that gids are also valid logids."""
    gid = get_gid("mygroup")
    assert is_logid(gid) is True
