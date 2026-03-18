from typing import Any

from pydantic import Field

from src.core import Dataclass
from src.core.util import multiline


class GraphInitParams(Dataclass):
    """Initialization params for a graph."""

    nodes: tuple[Any, ...] = Field(
        default=(),
        description="Initial node IDs to populate the graph with.",
    )

    default_edge_data: Any = Field(
        default=None,
        description="Default data for edges when not explicitly specified.",
    )

    directed: bool = Field(
        default=False,
        description=multiline(
            """
            Whether edges are directed by default. If False, connect(a, b)
            also creates the reverse edge b -> a with the same data.
            """
        ),
    )
