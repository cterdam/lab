import itertools
from collections.abc import Hashable, Iterable, Iterator
from enum import StrEnum

from src import env, log
from src.core import Logger
from src.core.util import obj_id
from src.lib.graph.graph_init_params import GraphInitParams


class Graph(Logger):
    """A weighted, optionally directed graph with logged mutations.

    Nodes are identified by any hashable value. Edges carry a non-negative
    cost. By default edges are bidirectional; this can be changed globally
    via ``GraphInitParams.directed`` or per-call via the ``directed`` kwarg
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
        EDGE_ADD = "+ edge {a} -> {b} (cost={cost})"
        EDGE_REMOVE = "- edge {a} -> {b}"

    # Adjacency: node -> {neighbor: cost}
    _adj: dict[Hashable, dict[Hashable, float]]

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
        self._adj = {}

        if nodes is not None:
            for node in nodes:
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

    def add_node(self, node: Hashable) -> None:
        """Add a node to the graph. No-op if already present."""
        if node in self._adj:
            self.incr(self.coke.ERR_NODE_EXISTS)
            self.warning(f"Node already exists: {node}")
            return
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
        self.incr(self.coke.REMOVE_NODE)
        self.debug(self.logmsg.NODE_REMOVE.format(node=node))

    # EDGE OPERATIONS ##########################################################

    def connect(
        self,
        a: Hashable,
        b: Hashable,
        cost: float | None = None,
        *,
        directed: bool | None = None,
    ) -> None:
        """Create an edge between two nodes.

        Args:
            a: Source node.
            b: Destination node.
            cost: Edge cost. Defaults to ``params.default_edge_cost``.
            directed: If True, only create a -> b. If None, use the graph
                default from ``params.directed``.
        """
        if a not in self._adj or b not in self._adj:
            missing = a if a not in self._adj else b
            self.incr(self.coke.ERR_NODE_MISSING)
            self.warning(f"Cannot connect, node not found: {missing}")
            return
        if cost is None:
            cost = self._params.default_edge_cost
        if directed is None:
            directed = self._params.directed

        self._adj[a][b] = cost
        if not directed:
            self._adj[b][a] = cost

        self.incr(self.coke.CONNECT)
        self.trace(self.logmsg.EDGE_ADD.format(a=a, b=b, cost=cost))

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
        max_cost: float | None = None,
    ) -> dict[Hashable, float]:
        """Return neighbors of a node with their edge costs.

        Args:
            node: The node to query.
            max_cost: If set, only return neighbors reachable within this cost.

        Returns:
            Dict mapping neighbor node IDs to edge costs.
        """
        if node not in self._adj:
            self.incr(self.coke.ERR_NODE_MISSING)
            self.warning(f"Node not found: {node}")
            return {}
        edges = self._adj[node]
        if max_cost is None:
            return dict(edges)
        return {n: c for n, c in edges.items() if c <= max_cost}

    def edge_cost(self, a: Hashable, b: Hashable) -> float | None:
        """Return the cost of edge a -> b, or None if no edge exists."""
        if a not in self._adj:
            return None
        return self._adj[a].get(b)

    def degree(self, node: Hashable) -> int:
        """Return the number of outgoing edges from a node."""
        if node not in self._adj:
            return 0
        return len(self._adj[node])

    # ITERATION ################################################################

    def iter_edges(self) -> Iterator[tuple[Hashable, Hashable, float]]:
        """Iterate over all edges as (source, dest, cost) tuples.

        For undirected graphs, each edge appears twice (a->b and b->a).
        """
        for node, edges in self._adj.items():
            for neighbor, cost in edges.items():
                yield node, neighbor, cost

    # FACTORY CLASSMETHODS #####################################################

    @classmethod
    def grid(
        cls,
        shape: tuple[int, ...],
        *,
        wrap: tuple[bool, ...] | None = None,
        edge_cost: float = 1.0,
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
            edge_cost: Cost for all grid edges.
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
            default_edge_cost=edge_cost,
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
                            coord, edge_cost
                        )
                        g._adj[coord].setdefault(
                            tuple(neighbor), edge_cost
                        )
                    elif wrap[axis]:
                        neighbor = list(coord)
                        neighbor[axis] = neighbor_val % shape[axis]
                        ntuple = tuple(neighbor)
                        if ntuple == coord:
                            continue  # skip self-loops from wrapping
                        g._adj[ntuple].setdefault(
                            coord, edge_cost
                        )
                        g._adj[coord].setdefault(
                            ntuple, edge_cost
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
