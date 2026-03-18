from typing import Any

from pydantic import Field

from src.core import Dataclass


class GraphInitParams(Dataclass):
    """Initialization params for a graph.

    This is the sole configuration object for ``Graph.__init__`` (besides
    ``logname``). Nodes are not specified here — use ``Graph.add()`` after
    construction, or a factory like ``Graph.grid()`` which populates
    nodes internally.
    """

    default_edge_data: Any = Field(
        default=None,
        description="Default data for edges when not explicitly specified.",
    )
