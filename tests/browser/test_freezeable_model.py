import pytest
from pydantic import Field

from getgather.browser.freezable_model import FreezableModel


class ExampleModel(FreezableModel):
    """Test model for freezing functionality."""

    value: str = Field(default="default")
    optional_value: str | None = Field(default=None)


def test_model_initial_state():
    """Test that model starts unfrozen and accepts changes."""
    model = ExampleModel()
    assert model.value == "default"

    # Should be able to modify attributes initially
    model.value = "modified"
    assert model.value == "modified"


def test_model_freeze():
    """Test that freezing prevents attribute changes."""
    model = ExampleModel()
    model.freeze()

    # Verify model is frozen
    with pytest.raises(TypeError) as excinfo:
        model.value = "should fail"
    assert "ExampleModel is frozen" in str(excinfo.value)
    assert "cannot set 'value'" in str(excinfo.value)


def test_model_delete_attr():
    """Test that freezing prevents attribute deletion."""
    model = ExampleModel()

    # Verify we can delete before freezing (if supported)
    # Note: Pydantic models typically don't allow attribute deletion,
    # but we test the functionality of our freezing mechanism

    model.freeze()

    # Verify frozen model prevents deletion
    with pytest.raises(TypeError) as excinfo:
        del model.value
    assert "ExampleModel is frozen" in str(excinfo.value)
    assert "cannot delete 'value'" in str(excinfo.value)


def test_model_nested_operations():
    """Test more complex scenarios with the freezable model."""
    model = ExampleModel(value="initial", optional_value="optional")

    # Modify before freezing
    model.value = "before_freeze"
    assert model.value == "before_freeze"

    model.freeze()

    # Try multiple operations on frozen model
    with pytest.raises(TypeError):
        model.value = "after_freeze"

    with pytest.raises(TypeError):
        model.optional_value = "new_optional"

    # Ensure values didn't change
    assert model.value == "before_freeze"
    assert model.optional_value == "optional"
