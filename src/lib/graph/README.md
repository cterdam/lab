# Graph

A general-purpose graph data structure built on `Logger`. Nodes and edges carry
arbitrary data. Edges are undirected by default but directionality can be
toggled globally or per-call. Designed as the foundation for higher-level
abstractions like game boards, maps, and networks.

## Design decisions

### Why a graph and not a board?

A board is just a graph with spatial semantics. Keeping the core structure
topology-agnostic means the same code handles hex grids, irregular maps, social
networks, or any other graph. A future `Board` subclass can layer spatial
concepts (coordinates, rendering, movement costs) on top.

### Adjacency dict representation

Internally the graph stores `_adj: dict[node, dict[neighbor, edge_data]]` and
`_nodes: dict[node, node_data]`. This gives O(1) edge lookup and O(degree)
neighbor iteration, which suits the typical board-game access pattern of
"what's around this tile?".

### No raising on bad input

Operations on missing nodes/edges are silent no-ops — they log a warning and
bump an error counter. This avoids crashing long-running game loops over a
stale reference. Check the error counters in the counter dump to catch bugs.

## Directionality

The `directed` flag on `GraphInitParams` sets the graph default. `connect` and
`disconnect` accept a `directed` kwarg to override per-call, enabling mixed
graphs (mostly undirected with a few one-way edges).

Internally, an undirected `connect(a, b)` writes two adjacency entries (a→b
and b→a) with the same data. These are independent dict entries — updating one
does not touch the other. `set_edge` is therefore always directional: it writes
only the a→b slot. To update both directions, call `set_edge` twice.

## Edge data and the `_UNSET` sentinel

`connect(a, b)` (no `data` arg) stores `params.default_edge_data` on the edge.
`connect(a, b, data=None)` explicitly stores `None`, even when the default is
non-None. This distinction matters for graphs where `None` is meaningful (e.g.
"no cost yet assigned"). It is implemented via an internal `_UNSET` sentinel
object — callers never interact with it directly.

## Grid factory

`Graph.grid(shape, ...)` builds an n-dimensional rectangular grid with
Manhattan (face-adjacent) connectivity. Nodes are coordinate tuples, e.g.
`(row, col)` for 2D or `(x, y, z)` for 3D.

### Wrapping

The `wrap` parameter is a per-axis bool tuple. `(True, False)` on a 2D grid
wraps rows (cylindrical); `(True, True)` wraps both axes (toroidal). Wrapping
connects boundary nodes to their opposite counterparts at construction time —
there is no runtime modular arithmetic on lookups. A single-cell axis with
wrapping enabled skips the would-be self-loop.

### Custom edge data

All grid edges receive the same `edge_data` value (default `1.0`). For
non-uniform costs, construct the grid and then update individual edges with
`set_edge`.

## Filtering neighbors

`neighbors(node, where=...)` accepts an optional predicate over edge data.
This replaces a type-specific `max_cost` parameter — the caller decides what
filtering means:

```python
# Passable tiles (cost under 3)
g.neighbors(pos, where=lambda d: d < 3)

# Only edges tagged "road"
g.neighbors(pos, where=lambda d: d.get("type") == "road")
```

## Iteration

`edges()` yields `(source, dest, data)` for every adjacency entry. In an
undirected graph each logical edge appears twice (a→b and b→a). Filter or
deduplicate as needed.

## Extend

To build on top of Graph (e.g. a Board):

1. Subclass `Graph`.
2. Add spatial semantics (coordinate systems, distance metrics, rendering).
3. Use `GraphInitParams` as-is or subclass it with additional fields.
4. Factory classmethods (like `grid`) can be added for new topologies (hex,
   triangular, etc.).
