import pytest
from pydantic import ValidationError

from src.lib.graph.graph_init_params import GraphInitParams


def test_defaults():
    """Default params: undirected, None edge data, no nodes."""
    p = GraphInitParams()
    assert p.default_edge_data is None
    assert p.directed is False
    assert p.nodes == ()


def test_custom_values():
    """Custom params are stored correctly."""
    p = GraphInitParams(
        nodes=("a", "b"), default_edge_data=5.0, directed=True
    )
    assert p.nodes == ("a", "b")
    assert p.default_edge_data == 5.0
    assert p.directed is True


def test_arbitrary_edge_data():
    """default_edge_data accepts any type."""
    p = GraphInitParams(default_edge_data={"weight": 1, "label": "road"})
    assert p.default_edge_data == {"weight": 1, "label": "road"}

    p2 = GraphInitParams(default_edge_data="highway")
    assert p2.default_edge_data == "highway"

    p3 = GraphInitParams(default_edge_data=[1, 2, 3])
    assert p3.default_edge_data == [1, 2, 3]


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
