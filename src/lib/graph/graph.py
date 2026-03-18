import itertools
from collections.abc import Callable, Hashable, Iterator
from enum import StrEnum
from typing import Any

from src import env, log
from src.core import Logger
from src.core.util import obj_id
from src.lib.graph.graph_init_params import GraphInitParams

_UNSET = object()


class Graph(Logger):
    """An optionally directed graph with arbitrary node and edge data.

    Nodes are identified by any hashable value and can carry arbitrary
    content. Edges also carry arbitrary data (cost, label, weight, etc.).
    By default edges are directed; this can be changed globally via
    ``GraphInitParams(directed=False)`` or per-call via the ``directed``
    kwarg on ``connect`` / ``disconnect``. A directed graph can be
    converted to undirected after the fact with ``symmetrize()``.

    Directionality
    ~~~~~~~~~~~~~~
    The graph-level ``directed`` flag (from ``GraphInitParams``) sets the
    default (``True``). ``connect`` and ``disconnect`` accept a
    ``directed`` kwarg that overrides it per-call. This lets you model
    mixed graphs (e.g. mostly directed with a few two-way edges).

    ``symmetrize()`` adds missing reverse edges and flips the graph to
    undirected mode, so subsequent ``connect``/``disconnect`` calls
    default to bidirectional. Existing reverse edges are preserved.

    ``set_edge`` is always directional — it updates only the a→b slot.
    In an undirected graph, the a→b and b→a edges are independent dict
    entries that happen to be created together by ``connect``. If you
    need to update both directions, call ``set_edge`` twice.

    Sentinel behavior
    ~~~~~~~~~~~~~~~~~
    ``connect(a, b)`` (no ``data`` arg) uses ``params.default_edge_data``.
    ``connect(a, b, data=None)`` explicitly stores ``None`` on the edge,
    even if the default is non-None. This distinction is implemented via
    an internal ``_UNSET`` sentinel.

    Error handling
    ~~~~~~~~~~~~~~
    Operations on missing nodes/edges are no-ops: they log a warning and
    increment an error counter (``ERR_NODE_MISSING``, ``ERR_EDGE_MISSING``,
    etc.) rather than raising. This keeps the graph usable in pipelines
    where partial data is expected.

    Iteration
    ~~~~~~~~~
    ``edges()`` yields every adjacency entry. For undirected graphs this
    means each logical edge appears twice (a→b and b→a).

    ``neighbors()`` accepts an optional ``where`` predicate over edge data
    for type-agnostic filtering (e.g. ``where=lambda d: d < 3``).

    Factory classmethods
    ~~~~~~~~~~~~~~~~~~~~
    ``Graph.grid(shape, ...)`` builds an n-dimensional rectangular grid.
    Wrapping (toroidal, cylindrical) is per-axis. Wrapping connects
    opposite boundary nodes at construction time — there is no runtime
    wrap check. A 1-cell axis with wrapping skips the self-loop.
    """

    logspace_part = "graph"

    class _coke(StrEnum):
        ADD = "add"
        RM = "rm"
        CONNECT = "connect"
        DISCONNECT = "disconnect"
        SYMMETRIZE = "symmetrize"
        ERR_NODE_EXISTS = obj_id(env.ERR_COKE_PREFIX, "node_exists")
        ERR_NODE_MISSING = obj_id(env.ERR_COKE_PREFIX, "node_missing")
        ERR_EDGE_MISSING = obj_id(env.ERR_COKE_PREFIX, "edge_missing")

    class _logmsg(StrEnum):
        GRAPH_INIT = "Graph created: {n} nodes, directed={directed}"
        NODE_ADD = "+ node {node}"
        NODE_RM = "- node {node}"
        EDGE_ADD = "+ edge {a} -> {b} (data={data})"
        EDGE_RM = "- edge {a} -> {b}"

    # Node data: node -> content
    _nodes: dict[Hashable, Any]

    # Adjacency: node -> {neighbor: edge_data}
    _adj: dict[Hashable, dict[Hashable, Any]]

    _params: GraphInitParams

    @log.input()
    def __init__(
        self,
        params: GraphInitParams,
        *args,
        logname: str = "graph",
        **kwargs,
    ):
        super().__init__(*args, logname=logname, **kwargs)
        self._params = params
        self._nodes = {}
        self._adj = {}

        self.info(
            self.logmsg.GRAPH_INIT.format(
                n=0,
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

    def has(self, node: Hashable) -> bool:
        """Check whether a node exists."""
        return node in self._adj

    def add(self, node: Hashable, data: Any = None) -> None:
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
        self.incr(self.coke.ADD)
        self.debug(self.logmsg.NODE_ADD.format(node=node))

    def rm(self, node: Hashable) -> None:
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
        self.incr(self.coke.RM)
        self.debug(self.logmsg.NODE_RM.format(node=node))

    def get_node(self, node: Hashable) -> Any:
        """Return the data stored on a node, or None if not found."""
        return self._nodes.get(node)

    def set_node(self, node: Hashable, data: Any) -> None:
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
        data: Any = _UNSET,
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
        if data is _UNSET:
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
        self.trace(self.logmsg.EDGE_RM.format(a=a, b=b))

    def symmetrize(self) -> None:
        """Add missing reverse edges to make all edges bidirectional.

        For every edge a→b, ensures b→a also exists with the same data.
        Existing reverse edges are not overwritten. After symmetrizing,
        the graph's directed flag is set to False so subsequent connect
        and disconnect calls default to undirected.
        """
        added = 0
        for node, adj in list(self._adj.items()):
            for neighbor, data in list(adj.items()):
                if neighbor in self._adj and node not in self._adj[neighbor]:
                    self._adj[neighbor][node] = data
                    added += 1
        self._params.directed = False
        self.incr(self.coke.SYMMETRIZE)
        self.info(f"Symmetrized: {added} reverse edges added, directed=False")

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
        adj = self._adj[node]
        if where is None:
            return dict(adj)
        return {n: d for n, d in adj.items() if where(d)}

    def get_edge(self, a: Hashable, b: Hashable) -> Any:
        """Return the data on edge a -> b, or None if no edge exists."""
        if a not in self._adj:
            return None
        return self._adj[a].get(b)

    def set_edge(self, a: Hashable, b: Hashable, data: Any) -> None:
        """Update data on an existing edge. No-op if edge does not exist."""
        if a not in self._adj or b not in self._adj.get(a, {}):
            self.incr(self.coke.ERR_EDGE_MISSING)
            self.warning(f"Edge not found: {a} -> {b}")
            return
        self._adj[a][b] = data

    def degree(self, node: Hashable) -> int:
        """Return the number of outgoing edges from a node."""
        if node not in self._adj:
            return 0
        return len(self._adj[node])

    # ITERATION ################################################################

    def edges(self) -> Iterator[tuple[Hashable, Hashable, Any]]:
        """Iterate over all edges as (source, dest, data) tuples.

        For undirected graphs, each edge appears twice (a->b and b->a).
        """
        for node, adj in self._adj.items():
            for neighbor, data in adj.items():
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

        params = kwargs.pop("params", None) or GraphInitParams(
            default_edge_data=edge_data,
            directed=False,
        )
        g = cls(params, logname=logname, **kwargs)

        # Create all coordinate nodes
        coords = list(itertools.product(*(range(d) for d in shape)))
        for coord in coords:
            g._nodes[coord] = None
            g._adj[coord] = {}
        g.incr(g.coke.ADD, len(coords))

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

        n_edges = sum(len(adj) for adj in g._adj.values())
        g.info(
            f"Grid {shape} created: {len(coords)} nodes, "
            f"{n_edges} directed edges, wrap={wrap}"
        )
        return g

    # CLEANUP ##################################################################

    def __del__(self):
        super().__del__()
