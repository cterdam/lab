from datetime import timedelta

import pytest
from pydantic import Field

from src.core.dataclass import Dataclass


# Simple test class that inherits from Dataclass
class SampleDataclass(Dataclass):
    """Test class for Dataclass protected fields."""

    value: str = Field(
        default="test",
        description="A test field.",
    )


def test_cls_automatically_set():
    """Test that cls is automatically set to the fully qualified class name."""
    obj = SampleDataclass()
    assert obj.cls == "test.core.test_dataclass.SampleDataclass"
    assert isinstance(obj.cls, str)


def test_cannot_assign_to_cls_after_initialization():
    """Test that assigning to cls after initialization raises ValueError."""
    obj = SampleDataclass()
    original_cls = obj.cls

    with pytest.raises(ValueError, match="Cannot assign to 'cls' field"):
        obj.cls = "wrong.value"

    # Verify cls was not changed
    assert obj.cls == original_cls


def test_sid_automatically_generated():
    """Test that sid is automatically generated."""
    obj1 = SampleDataclass()
    obj2 = SampleDataclass()

    assert obj1.sid is not None
    assert obj2.sid is not None
    assert isinstance(obj1.sid, int)
    assert obj1.sid != obj2.sid  # Each instance should have unique sid


def test_cannot_assign_to_sid_after_initialization():
    """Test that assigning to sid after initialization raises ValueError."""
    obj = SampleDataclass()
    original_sid = obj.sid

    with pytest.raises(ValueError, match="Cannot assign to 'sid' field"):
        obj.sid = 999

    # Verify sid was not changed
    assert obj.sid == original_sid


def test_normal_fields_work_correctly():
    """Test that normal fields can be set and modified."""
    obj = SampleDataclass(value="initial")
    assert obj.value == "initial"

    obj.value = "modified"
    assert obj.value == "modified"


def test_can_provide_other_fields_during_initialization():
    """Test that other fields can be provided during initialization."""
    obj = SampleDataclass(value="custom_value")
    assert obj.value == "custom_value"
    assert obj.cls == "test.core.test_dataclass.SampleDataclass"
    assert obj.sid is not None


def test_cls_set_correctly_for_different_classes():
    """Test that cls is set correctly for different Dataclass subclasses."""
    from src.core.func_result import Timed
    from src.lib.game.game_init_params import GameInitParams

    game_params = GameInitParams()
    assert game_params.cls == "src.lib.game.game_init_params.GameInitParams"

    timed_result = Timed[SampleDataclass](data=SampleDataclass())
    assert timed_result.cls == "src.core.func_result.Timed[SampleDataclass]"


def test_cls_matches_during_assignment_validation():
    """Test that cls validation works correctly during assignment validation.

    This tests that when validate_assignment=True triggers re-validation,
    the cls field (which matches expected) is allowed through.
    """
    obj = SampleDataclass(value="initial")
    original_cls = obj.cls

    # This should work - setting a different field triggers validation
    # but cls should remain valid since it matches expected
    obj.value = "new_value"

    assert obj.cls == original_cls
    assert obj.value == "new_value"
