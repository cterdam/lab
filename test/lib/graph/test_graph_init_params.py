import pytest
from pydantic import ValidationError

from src.lib.graph.graph_init_params import GraphInitParams


def test_defaults():
    """Default params: undirected, cost 1.0."""
    p = GraphInitParams()
    assert p.default_edge_cost == 1.0
    assert p.directed is False


def test_custom_values():
    """Custom params are stored correctly."""
    p = GraphInitParams(default_edge_cost=5.0, directed=True)
    assert p.default_edge_cost == 5.0
    assert p.directed is True


def test_negative_cost_rejected():
    """Negative edge cost is rejected."""
    with pytest.raises(ValidationError):
        GraphInitParams(default_edge_cost=-1.0)


def test_zero_cost_accepted():
    """Zero edge cost is valid."""
    p = GraphInitParams(default_edge_cost=0.0)
    assert p.default_edge_cost == 0.0


def test_has_sid():
    """As a Dataclass, it has auto-generated sid and cls fields."""
    p = GraphInitParams()
    assert hasattr(p, "sid")
    assert hasattr(p, "cls")
    assert "GraphInitParams" in p.cls


def test_extra_fields_forbidden():
    """Extra fields are rejected (Dataclass uses extra='forbid')."""
    with pytest.raises(ValidationError):
        GraphInitParams(unknown_field="oops")
