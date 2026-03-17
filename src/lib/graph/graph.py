import itertools
from collections.abc import Callable, Hashable, Iterable, Iterator
from enum import StrEnum
from typing import Any

from src import env, log
from src.core import Logger
from src.core.util import obj_id
from src.lib.graph.graph_init_params import GraphInitParams


class Graph(Logger):
    """An optionally directed graph with arbitrary node and edge data.

    Nodes are identified by any hashable value and can carry arbitrary
    content. Edges also carry arbitrary data (cost, label, weight, etc.).
    By default edges are bidirectional; this can be changed globally via
    ``GraphInitParams.directed`` or per-call via the ``directed`` kwarg
    on ``connect`` / ``disconnect``.

    Common topologies can be constructed via factory classmethods such as
    ``Graph.grid``.
    """

    logspace_part = "graph"

    class _coke(StrEnum):
        ADD_NODE = "add_node"
        REMOVE_NODE = "remove_node"
        CONNECT = "connect"
        DISCONNECT = "disconnect"
        ERR_NODE_EXISTS = obj_id(env.ERR_COKE_PREFIX, "node_exists")
        ERR_NODE_MISSING = obj_id(env.ERR_COKE_PREFIX, "node_missing")

    class _logmsg(StrEnum):
        GRAPH_INIT = "Graph created: {n_nodes} nodes, directed={directed}"
        NODE_ADD = "+ node {node}"
        NODE_REMOVE = "- node {node}"
        EDGE_ADD = "+ edge {a} -> {b} (data={data})"
        EDGE_REMOVE = "- edge {a} -> {b}"

    # Node data: node -> content
    _nodes: dict[Hashable, Any]

    # Adjacency: node -> {neighbor: edge_data}
    _adj: dict[Hashable, dict[Hashable, Any]]

    _params: GraphInitParams

    @log.input()
    def __init__(
        self,
        params: GraphInitParams | None = None,
        *args,
        nodes: Iterable[Hashable] | None = None,
        logname: str = "graph",
        **kwargs,
    ):
        super().__init__(*args, logname=logname, **kwargs)
        self._params = params or GraphInitParams()
        self._nodes = {}
        self._adj = {}

        if nodes is not None:
            for node in nodes:
                self._nodes[node] = None
                self._adj[node] = {}
            self.incr(self.coke.ADD_NODE, len(self._adj))

        self.info(
            self.logmsg.GRAPH_INIT.format(
                n_nodes=len(self._adj),
                directed=self._params.directed,
            )
        )

    # PROPERTIES ###############################################################

    @property
    def _logtag(self) -> str:
        return f"{len(self._adj)}n"

    @property
    def n_nodes(self) -> int:
        """Number of nodes in the graph."""
        return len(self._adj)

    @property
    def nodes(self) -> frozenset[Hashable]:
        """All node IDs."""
        return frozenset(self._adj)

    @property
    def directed(self) -> bool:
        """Whether the graph defaults to directed edges."""
        return self._params.directed

    # NODE OPERATIONS ##########################################################

    def has_node(self, node: Hashable) -> bool:
        """Check whether a node exists."""
        return node in self._adj

    def add_node(self, node: Hashable, data: Any = None) -> None:
        """Add a node to the graph. No-op if already present.

        Args:
            node: Hashable node identifier.
            data: Arbitrary content to store on the node.
        """
        if node in self._adj:
            self.incr(self.coke.ERR_NODE_EXISTS)
            self.warning(f"Node already exists: {node}")
            return
        self._nodes[node] = data
        self._adj[node] = {}
        self.incr(self.coke.ADD_NODE)
        self.debug(self.logmsg.NODE_ADD.format(node=node))

    def remove_node(self, node: Hashable) -> None:
        """Remove a node and all its edges."""
        if node not in self._adj:
            self.incr(self.coke.ERR_NODE_MISSING)
            self.warning(f"Node not found: {node}")
            return
        # Remove all edges pointing to this node
        for neighbor in list(self._adj[node]):
            self._adj[neighbor].pop(node, None)
        del self._adj[node]
        del self._nodes[node]
        self.incr(self.coke.REMOVE_NODE)
        self.debug(self.logmsg.NODE_REMOVE.format(node=node))

    def node_data(self, node: Hashable) -> Any:
        """Return the data stored on a node, or None if node not found."""
        return self._nodes.get(node)

    def set_node_data(self, node: Hashable, data: Any) -> None:
        """Update the data stored on an existing node."""
        if node not in self._adj:
            self.incr(self.coke.ERR_NODE_MISSING)
            self.warning(f"Node not found: {node}")
            return
        self._nodes[node] = data

    # EDGE OPERATIONS ##########################################################

    def connect(
        self,
        a: Hashable,
        b: Hashable,
        data: Any = None,
        *,
        directed: bool | None = None,
    ) -> None:
        """Create an edge between two nodes.

        Args:
            a: Source node.
            b: Destination node.
            data: Arbitrary edge data. Defaults to
                ``params.default_edge_data``.
            directed: If True, only create a -> b. If None, use the graph
                default from ``params.directed``.
        """
        if a not in self._adj or b not in self._adj:
            missing = a if a not in self._adj else b
            self.incr(self.coke.ERR_NODE_MISSING)
            self.warning(f"Cannot connect, node not found: {missing}")
            return
        if data is None:
            data = self._params.default_edge_data
        if directed is None:
            directed = self._params.directed

        self._adj[a][b] = data
        if not directed:
            self._adj[b][a] = data

        self.incr(self.coke.CONNECT)
        self.trace(self.logmsg.EDGE_ADD.format(a=a, b=b, data=data))

    def disconnect(
        self,
        a: Hashable,
        b: Hashable,
        *,
        directed: bool | None = None,
    ) -> None:
        """Remove an edge between two nodes.

        Args:
            a: Source node.
            b: Destination node.
            directed: If True, only remove a -> b. If None, use the graph
                default from ``params.directed``.
        """
        if a not in self._adj or b not in self._adj:
            missing = a if a not in self._adj else b
            self.incr(self.coke.ERR_NODE_MISSING)
            self.warning(f"Cannot disconnect, node not found: {missing}")
            return
        if directed is None:
            directed = self._params.directed

        self._adj[a].pop(b, None)
        if not directed:
            self._adj[b].pop(a, None)

        self.incr(self.coke.DISCONNECT)
        self.trace(self.logmsg.EDGE_REMOVE.format(a=a, b=b))

    # QUERY OPERATIONS #########################################################

    def neighbors(
        self,
        node: Hashable,
        *,
        where: Callable[[Any], bool] | None = None,
    ) -> dict[Hashable, Any]:
        """Return neighbors of a node with their edge data.

        Args:
            node: The node to query.
            where: Optional predicate on edge data. Only neighbors whose
                edge data satisfies the predicate are returned.

        Returns:
            Dict mapping neighbor node IDs to edge data.
        """
        if node not in self._adj:
            self.incr(self.coke.ERR_NODE_MISSING)
            self.warning(f"Node not found: {node}")
            return {}
        edges = self._adj[node]
        if where is None:
            return dict(edges)
        return {n: d for n, d in edges.items() if where(d)}

    def edge_data(self, a: Hashable, b: Hashable) -> Any:
        """Return the data on edge a -> b, or None if no edge exists."""
        if a not in self._adj:
            return None
        return self._adj[a].get(b)

    def degree(self, node: Hashable) -> int:
        """Return the number of outgoing edges from a node."""
        if node not in self._adj:
            return 0
        return len(self._adj[node])

    # ITERATION ################################################################

    def iter_edges(self) -> Iterator[tuple[Hashable, Hashable, Any]]:
        """Iterate over all edges as (source, dest, data) tuples.

        For undirected graphs, each edge appears twice (a->b and b->a).
        """
        for node, edges in self._adj.items():
            for neighbor, data in edges.items():
                yield node, neighbor, data

    # FACTORY CLASSMETHODS #####################################################

    @classmethod
    def grid(
        cls,
        shape: tuple[int, ...],
        *,
        wrap: tuple[bool, ...] | None = None,
        edge_data: Any = 1.0,
        logname: str = "grid",
        **kwargs,
    ) -> "Graph":
        """Create a rectangular n-dimensional grid graph.

        Nodes are coordinate tuples, e.g. (row, col) for 2D. Each node is
        connected to its face-adjacent neighbors (Manhattan connectivity).

        Args:
            shape: Size along each dimension, e.g. ``(8, 8)`` for a chessboard.
            wrap: Per-axis wrapping. ``(True, False)`` wraps the first axis
                only (cylindrical). Defaults to no wrapping on any axis.
            edge_data: Data for all grid edges. Defaults to ``1.0``.
            logname: Logger name.
            **kwargs: Passed to ``__init__`` (and then to ``Logger``).

        Returns:
            A Graph with grid topology.
        """
        ndim = len(shape)
        if wrap is None:
            wrap = tuple(False for _ in range(ndim))
        if len(wrap) != ndim:
            raise ValueError(
                f"wrap length {len(wrap)} != shape dimensions {ndim}"
            )

        # Create all coordinate nodes
        coords = list(itertools.product(*(range(d) for d in shape)))
        params = kwargs.pop("params", None) or GraphInitParams(
            default_edge_data=edge_data,
        )
        g = cls(params, nodes=coords, logname=logname, **kwargs)

        # Connect face-adjacent neighbors
        for coord in coords:
            for axis in range(ndim):
                for delta in (-1, 1):
                    neighbor_val = coord[axis] + delta
                    if 0 <= neighbor_val < shape[axis]:
                        neighbor = list(coord)
                        neighbor[axis] = neighbor_val
                        g._adj[tuple(neighbor)].setdefault(
                            coord, edge_data
                        )
                        g._adj[coord].setdefault(
                            tuple(neighbor), edge_data
                        )
                    elif wrap[axis]:
                        neighbor = list(coord)
                        neighbor[axis] = neighbor_val % shape[axis]
                        ntuple = tuple(neighbor)
                        if ntuple == coord:
                            continue  # skip self-loops from wrapping
                        g._adj[ntuple].setdefault(
                            coord, edge_data
                        )
                        g._adj[coord].setdefault(
                            ntuple, edge_data
                        )

        n_edges = sum(len(edges) for edges in g._adj.values())
        g.info(
            f"Grid {shape} created: {len(coords)} nodes, "
            f"{n_edges} directed edges, wrap={wrap}"
        )
        return g

    # CLEANUP ##################################################################

    def __del__(self):
        super().__del__()
