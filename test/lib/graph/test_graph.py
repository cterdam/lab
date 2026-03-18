import gc
import weakref

import pytest

from src.lib.graph.graph import Graph
from src.lib.graph.graph_init_params import GraphInitParams


# INIT & LIFECYCLE #############################################################


def test_empty_graph():
    """A graph with no nodes is valid."""
    g = Graph(GraphInitParams(), logname="test_empty")
    assert g.n_nodes == 0
    assert g.nodes == frozenset()


def test_init_with_nodes():
    """Nodes passed via params are registered."""
    p = GraphInitParams(nodes=("a", "b", "c"))
    g = Graph(p, logname="test_init_nodes")
    assert g.n_nodes == 3
    assert g.nodes == frozenset({"a", "b", "c"})


def test_init_default_params():
    """Default params give undirected graph with None edge data."""
    g = Graph(GraphInitParams(), logname="test_default_params")
    assert g.directed is False
    assert g._params.default_edge_data is None


def test_init_custom_params():
    """Custom params are respected."""
    p = GraphInitParams(default_edge_data=2.5, directed=True)
    g = Graph(p, logname="test_custom_params")
    assert g.directed is True
    assert g._params.default_edge_data == 2.5


def test_logtag():
    """_logtag shows node count."""
    p = GraphInitParams(nodes=(1, 2, 3))
    g = Graph(p, logname="test_logtag")
    assert g._logtag == "3n"


def test_logspace():
    """logspace_part is 'graph'."""
    g = Graph(GraphInitParams(), logname="test_logspace")
    assert "graph" in g.logspace


def test_cleanup():
    """Graph instance is garbage collected cleanly."""
    p = GraphInitParams(nodes=(1, 2))
    g = Graph(p, logname="test_gc")
    weak = weakref.ref(g)
    del g
    gc.collect()
    assert weak() is None


# NODE OPERATIONS ##############################################################


def test_add_node():
    """add_node registers a new node."""
    g = Graph(GraphInitParams(), logname="test_add_node")
    g.add_node("x")
    assert g.has_node("x")
    assert g.n_nodes == 1


def test_add_node_with_data():
    """add_node stores arbitrary data."""
    g = Graph(GraphInitParams(), logname="test_add_node_data")
    g.add_node("x", data={"color": "red", "hp": 100})
    assert g.node_data("x") == {"color": "red", "hp": 100}


def test_add_node_default_data_is_none():
    """Nodes without explicit data have None content."""
    p = GraphInitParams(nodes=("a",))
    g = Graph(p, logname="test_node_default")
    assert g.node_data("a") is None


def test_add_node_duplicate():
    """Adding an existing node is a no-op (with warning)."""
    p = GraphInitParams(nodes=("x",))
    g = Graph(p, logname="test_add_dup")
    g.add_node("x")
    assert g.n_nodes == 1


def test_remove_node():
    """Removing a node deletes it and its edges."""
    p = GraphInitParams(nodes=("a", "b"))
    g = Graph(p, logname="test_rm_node")
    g.connect("a", "b")
    g.remove_node("a")
    assert not g.has_node("a")
    assert g.neighbors("b") == {}


def test_remove_node_clears_data():
    """Removing a node also removes its data."""
    g = Graph(GraphInitParams(), logname="test_rm_data")
    g.add_node("x", data="important")
    g.remove_node("x")
    assert g.node_data("x") is None


def test_remove_node_missing():
    """Removing a non-existent node is a no-op."""
    g = Graph(GraphInitParams(), logname="test_rm_missing")
    g.remove_node("nope")  # should not raise
    assert g.n_nodes == 0


def test_has_node():
    """has_node returns correct bool."""
    p = GraphInitParams(nodes=("a",))
    g = Graph(p, logname="test_has")
    assert g.has_node("a")
    assert not g.has_node("z")


def test_add_node_various_types():
    """Nodes can be any hashable type."""
    g = Graph(GraphInitParams(), logname="test_types")
    g.add_node(42)
    g.add_node("hello")
    g.add_node((1, 2, 3))
    assert g.n_nodes == 3
    assert g.has_node(42)
    assert g.has_node("hello")
    assert g.has_node((1, 2, 3))


def test_node_data():
    """node_data retrieves stored content."""
    g = Graph(GraphInitParams(), logname="test_node_data")
    g.add_node("a", data=[1, 2, 3])
    assert g.node_data("a") == [1, 2, 3]


def test_node_data_missing():
    """node_data returns None for non-existent node."""
    g = Graph(GraphInitParams(), logname="test_node_data_miss")
    assert g.node_data("nope") is None


def test_set_node_data():
    """set_node_data updates existing node content."""
    g = Graph(GraphInitParams(), logname="test_set_data")
    g.add_node("a", data="old")
    g.set_node_data("a", "new")
    assert g.node_data("a") == "new"


def test_set_node_data_missing():
    """set_node_data on non-existent node is a no-op."""
    g = Graph(GraphInitParams(), logname="test_set_data_miss")
    g.set_node_data("nope", "value")  # should not raise


def test_node_data_complex_objects():
    """Nodes can hold complex objects."""
    g = Graph(GraphInitParams(), logname="test_complex_node")

    class Piece:
        def __init__(self, name):
            self.name = name

    piece = Piece("knight")
    g.add_node("e4", data=piece)
    assert g.node_data("e4").name == "knight"


# EDGE OPERATIONS ##############################################################


def test_connect_undirected():
    """Undirected connect creates edges in both directions."""
    p = GraphInitParams(nodes=("a", "b"), default_edge_data=1.0)
    g = Graph(p, logname="test_connect_undir")
    g.connect("a", "b")
    assert g.edge_data("a", "b") == 1.0
    assert g.edge_data("b", "a") == 1.0


def test_connect_directed():
    """Directed connect creates edge in one direction only."""
    p = GraphInitParams(nodes=("a", "b"), directed=True, default_edge_data=1.0)
    g = Graph(p, logname="test_connect_dir")
    g.connect("a", "b")
    assert g.edge_data("a", "b") == 1.0
    assert g.edge_data("b", "a") is None


def test_connect_directed_override():
    """Per-call directed flag overrides graph default."""
    p = GraphInitParams(nodes=("a", "b"), default_edge_data=1.0)
    g = Graph(p, logname="test_dir_override")
    g.connect("a", "b", directed=True)
    assert g.edge_data("a", "b") == 1.0
    assert g.edge_data("b", "a") is None


def test_connect_undirected_override():
    """Per-call directed=False overrides directed graph."""
    p = GraphInitParams(
        nodes=("a", "b"), directed=True, default_edge_data=1.0
    )
    g = Graph(p, logname="test_undir_override")
    g.connect("a", "b", directed=False)
    assert g.edge_data("a", "b") == 1.0
    assert g.edge_data("b", "a") == 1.0


def test_connect_custom_data():
    """Custom edge data is stored."""
    p = GraphInitParams(nodes=("a", "b"))
    g = Graph(p, logname="test_data")
    g.connect("a", "b", data=3.5)
    assert g.edge_data("a", "b") == 3.5
    assert g.edge_data("b", "a") == 3.5


def test_connect_dict_data():
    """Edges can carry dict data."""
    p = GraphInitParams(nodes=("a", "b"))
    g = Graph(p, logname="test_dict_edge")
    g.connect("a", "b", data={"weight": 5, "label": "road"})
    assert g.edge_data("a", "b") == {"weight": 5, "label": "road"}


def test_connect_string_data():
    """Edges can carry string data."""
    p = GraphInitParams(nodes=("a", "b"))
    g = Graph(p, logname="test_str_edge")
    g.connect("a", "b", data="highway")
    assert g.edge_data("a", "b") == "highway"


def test_connect_explicit_none_data():
    """Explicitly passing data=None stores None, not the default."""
    p = GraphInitParams(nodes=("a", "b"), default_edge_data=99)
    g = Graph(p, logname="test_explicit_none")
    g.connect("a", "b", data=None)
    assert g.edge_data("a", "b") is None


def test_connect_missing_node():
    """Connecting to a non-existent node is a no-op."""
    p = GraphInitParams(nodes=("a",))
    g = Graph(p, logname="test_connect_missing")
    g.connect("a", "b")  # b doesn't exist
    assert g.neighbors("a") == {}


def test_disconnect_undirected():
    """Undirected disconnect removes edges in both directions."""
    p = GraphInitParams(nodes=("a", "b"))
    g = Graph(p, logname="test_disconnect_undir")
    g.connect("a", "b", data=1.0)
    g.disconnect("a", "b")
    assert g.edge_data("a", "b") is None
    assert g.edge_data("b", "a") is None


def test_disconnect_directed():
    """Directed disconnect only removes a -> b."""
    p = GraphInitParams(nodes=("a", "b"))
    g = Graph(p, logname="test_disconnect_dir")
    g.connect("a", "b", data=1.0, directed=False)
    g.disconnect("a", "b", directed=True)
    assert g.edge_data("a", "b") is None
    assert g.edge_data("b", "a") == 1.0


def test_disconnect_missing_node():
    """Disconnecting non-existent nodes is a no-op."""
    g = Graph(GraphInitParams(), logname="test_disc_missing")
    g.disconnect("a", "b")  # neither exists


def test_disconnect_no_edge():
    """Disconnecting nodes with no edge is a no-op."""
    p = GraphInitParams(nodes=("a", "b"))
    g = Graph(p, logname="test_disc_no_edge")
    g.disconnect("a", "b")  # no edge, should not raise


def test_connect_overwrites_data():
    """Connecting again overwrites the edge data."""
    p = GraphInitParams(nodes=("a", "b"))
    g = Graph(p, logname="test_overwrite")
    g.connect("a", "b", data=1.0)
    g.connect("a", "b", data=5.0)
    assert g.edge_data("a", "b") == 5.0


def test_connect_default_data_is_none():
    """Without default_edge_data, edge data defaults to None."""
    p = GraphInitParams(nodes=("a", "b"))
    g = Graph(p, logname="test_default_edge")
    g.connect("a", "b")
    assert g.edge_data("a", "b") is None


# QUERY OPERATIONS #############################################################


def test_neighbors():
    """neighbors returns dict of neighbor -> data."""
    p = GraphInitParams(nodes=("a", "b", "c"), default_edge_data=0)
    g = Graph(p, logname="test_neighbors")
    g.connect("a", "b", data=1.0)
    g.connect("a", "c", data=2.0)
    n = g.neighbors("a")
    assert n == {"b": 1.0, "c": 2.0}


def test_neighbors_where():
    """where predicate filters neighbors by edge data."""
    p = GraphInitParams(nodes=("a", "b", "c"))
    g = Graph(p, logname="test_where")
    g.connect("a", "b", data=1.0)
    g.connect("a", "c", data=5.0)
    n = g.neighbors("a", where=lambda d: d <= 2.0)
    assert n == {"b": 1.0}


def test_neighbors_where_complex():
    """where predicate works with complex edge data."""
    p = GraphInitParams(nodes=("a", "b", "c"))
    g = Graph(p, logname="test_where_complex")
    g.connect("a", "b", data={"type": "road", "cost": 1})
    g.connect("a", "c", data={"type": "river", "cost": 5})
    roads = g.neighbors("a", where=lambda d: d["type"] == "road")
    assert set(roads.keys()) == {"b"}


def test_neighbors_missing_node():
    """neighbors on non-existent node returns empty dict."""
    g = Graph(GraphInitParams(), logname="test_neighbors_missing")
    assert g.neighbors("nope") == {}


def test_edge_data_no_edge():
    """edge_data returns None when no edge exists."""
    p = GraphInitParams(nodes=("a", "b"))
    g = Graph(p, logname="test_edge_no")
    assert g.edge_data("a", "b") is None


def test_edge_data_no_node():
    """edge_data returns None when source node doesn't exist."""
    g = Graph(GraphInitParams(), logname="test_edge_no_node")
    assert g.edge_data("x", "y") is None


def test_degree():
    """degree returns outgoing edge count."""
    p = GraphInitParams(nodes=("a", "b", "c"))
    g = Graph(p, logname="test_degree")
    g.connect("a", "b", data=1)
    g.connect("a", "c", data=1)
    assert g.degree("a") == 2


def test_degree_missing():
    """degree of non-existent node is 0."""
    g = Graph(GraphInitParams(), logname="test_degree_miss")
    assert g.degree("x") == 0


def test_degree_directed():
    """In a directed graph, degree only counts outgoing."""
    p = GraphInitParams(nodes=("a", "b"), directed=True, default_edge_data=1)
    g = Graph(p, logname="test_degree_dir")
    g.connect("a", "b")
    assert g.degree("a") == 1
    assert g.degree("b") == 0


# ITERATION ####################################################################


def test_iter_edges():
    """iter_edges yields all directed edge tuples."""
    p = GraphInitParams(nodes=("a", "b"))
    g = Graph(p, logname="test_iter")
    g.connect("a", "b", data=2.0)
    edges = list(g.iter_edges())
    # Undirected: a->b and b->a
    assert ("a", "b", 2.0) in edges
    assert ("b", "a", 2.0) in edges
    assert len(edges) == 2


def test_iter_edges_directed():
    """iter_edges on directed graph yields one-way edges."""
    p = GraphInitParams(nodes=("a", "b"), directed=True)
    g = Graph(p, logname="test_iter_dir")
    g.connect("a", "b", data=1.0)
    edges = list(g.iter_edges())
    assert edges == [("a", "b", 1.0)]


def test_iter_edges_empty():
    """iter_edges on empty graph yields nothing."""
    g = Graph(GraphInitParams(), logname="test_iter_empty")
    assert list(g.iter_edges()) == []


# GRID FACTORY #################################################################


def test_grid_1d():
    """1D grid: linear chain."""
    g = Graph.grid((5,), logname="test_grid_1d")
    assert g.n_nodes == 5
    # Middle node has 2 neighbors
    assert g.degree((2,)) == 2
    # End nodes have 1 neighbor
    assert g.degree((0,)) == 1
    assert g.degree((4,)) == 1


def test_grid_2d():
    """2D grid: standard rectangle."""
    g = Graph.grid((3, 4), logname="test_grid_2d")
    assert g.n_nodes == 12
    # Corner has 2 neighbors
    assert g.degree((0, 0)) == 2
    # Edge has 3 neighbors
    assert g.degree((0, 1)) == 3
    # Interior has 4 neighbors
    assert g.degree((1, 1)) == 4


def test_grid_3d():
    """3D grid works."""
    g = Graph.grid((2, 2, 2), logname="test_grid_3d")
    assert g.n_nodes == 8
    # Corner of 3D cube: 3 face-adjacent neighbors
    assert g.degree((0, 0, 0)) == 3


def test_grid_wrap_all():
    """Fully wrapped 2D grid (toroidal): every node has 4 neighbors."""
    g = Graph.grid((3, 3), wrap=(True, True), logname="test_grid_torus")
    assert g.n_nodes == 9
    for node in g.nodes:
        assert g.degree(node) == 4, f"Node {node} has degree {g.degree(node)}"


def test_grid_wrap_one_axis():
    """Cylindrical: wrap one axis only."""
    g = Graph.grid((3, 3), wrap=(True, False), logname="test_grid_cyl")
    # Top-left: wraps on axis 0, not axis 1
    # axis 0 neighbors: (2,0) and (1,0) -- both exist due to wrap
    # axis 1 neighbors: (0,1) only -- (0,-1) doesn't exist
    assert g.degree((0, 0)) == 3


def test_grid_1d_wrap():
    """1D wrapped grid: ring topology."""
    g = Graph.grid((5,), wrap=(True,), logname="test_grid_ring")
    # Every node has exactly 2 neighbors (ring)
    for node in g.nodes:
        assert g.degree(node) == 2
    # End connects to start
    assert g.edge_data((0,), (4,)) == 1.0
    assert g.edge_data((4,), (0,)) == 1.0


def test_grid_custom_edge_data():
    """Grid edges use the specified data."""
    g = Graph.grid((2, 2), edge_data=3.0, logname="test_grid_data")
    assert g.edge_data((0, 0), (0, 1)) == 3.0


def test_grid_non_numeric_edge_data():
    """Grid edges can carry non-numeric data."""
    g = Graph.grid((2, 2), edge_data="path", logname="test_grid_str")
    assert g.edge_data((0, 0), (0, 1)) == "path"


def test_grid_wrap_mismatch_raises():
    """wrap length must match shape dimensions."""
    with pytest.raises(ValueError, match="wrap length"):
        Graph.grid((3, 3), wrap=(True,), logname="test_grid_mismatch")


def test_grid_single_cell():
    """1x1 grid: single node, no edges."""
    g = Graph.grid((1,), logname="test_grid_1x1")
    assert g.n_nodes == 1
    assert g.degree((0,)) == 0


def test_grid_single_cell_wrapped():
    """1x1 wrapped grid: self-loop doesn't happen (same node)."""
    g = Graph.grid((1,), wrap=(True,), logname="test_grid_1x1_wrap")
    assert g.n_nodes == 1
    # A node wrapping to itself should not create a self-edge
    assert g.degree((0,)) == 0


def test_grid_2x1_wrapped():
    """2x1 wrapped: two nodes connected, wrap connects same pair."""
    g = Graph.grid((2,), wrap=(True,), logname="test_grid_2x1_wrap")
    assert g.n_nodes == 2
    assert g.edge_data((0,), (1,)) == 1.0
    assert g.edge_data((1,), (0,)) == 1.0
    # Degree is still 1 since wrap connects same pair
    assert g.degree((0,)) == 1


# COMPLEX SCENARIOS ############################################################


def test_remove_node_cleans_all_edges():
    """Removing a highly-connected node cleans all inbound edges."""
    p = GraphInitParams(nodes=("hub", "a", "b", "c"))
    g = Graph(p, logname="test_rm_hub")
    g.connect("hub", "a", data=1)
    g.connect("hub", "b", data=1)
    g.connect("hub", "c", data=1)
    g.remove_node("hub")
    assert g.neighbors("a") == {}
    assert g.neighbors("b") == {}
    assert g.neighbors("c") == {}


def test_self_loop():
    """A node can connect to itself."""
    p = GraphInitParams(nodes=("a",))
    g = Graph(p, logname="test_self_loop")
    g.connect("a", "a", data=1)
    assert g.edge_data("a", "a") is not None
    assert g.degree("a") == 1


def test_nodes_property_immutable():
    """nodes property returns a frozenset (immutable)."""
    p = GraphInitParams(nodes=("a",))
    g = Graph(p, logname="test_frozen")
    ns = g.nodes
    assert isinstance(ns, frozenset)


def test_neighbors_returns_copy():
    """neighbors returns a copy, not a reference to internal state."""
    p = GraphInitParams(nodes=("a", "b"))
    g = Graph(p, logname="test_nbr_copy")
    g.connect("a", "b", data=1.0)
    n = g.neighbors("a")
    n["c"] = 99.0  # mutate returned dict
    assert "c" not in g.neighbors("a")  # internal state unchanged


def test_where_boundary():
    """where predicate at boundary: equal value is caller's choice."""
    p = GraphInitParams(nodes=("a", "b", "c"))
    g = Graph(p, logname="test_boundary")
    g.connect("a", "b", data=2.0)
    g.connect("a", "c", data=3.0)
    n = g.neighbors("a", where=lambda d: d <= 2.0)
    assert "b" in n
    assert "c" not in n


def test_zero_data_edge():
    """Edges with data 0 are valid and distinguishable from None."""
    p = GraphInitParams(nodes=("a", "b"))
    g = Graph(p, logname="test_zero_data")
    g.connect("a", "b", data=0)
    assert g.edge_data("a", "b") == 0
    assert g.edge_data("a", "b") is not None


def test_where_with_none_data():
    """where predicate can filter edges with None data."""
    p = GraphInitParams(nodes=("a", "b", "c"))
    g = Graph(p, logname="test_where_none")
    g.connect("a", "b", data="x")
    g.connect("a", "c")  # None data
    n = g.neighbors("a", where=lambda d: d is not None)
    assert set(n.keys()) == {"b"}
