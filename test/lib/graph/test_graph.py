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
    g = Graph(GraphInitParams(), logname="test_logtag")
    g.add(1)
    g.add(2)
    g.add(3)
    assert g._logtag == "3n"


def test_logspace():
    """logspace_part is 'graph'."""
    g = Graph(GraphInitParams(), logname="test_logspace")
    assert "graph" in g.logspace


def test_cleanup():
    """Graph instance is garbage collected cleanly."""
    g = Graph(GraphInitParams(), logname="test_gc")
    g.add(1)
    g.add(2)
    weak = weakref.ref(g)
    del g
    gc.collect()
    assert weak() is None


# NODE OPERATIONS ##############################################################


def test_add():
    """add registers a new node."""
    g = Graph(GraphInitParams(), logname="test_add")
    g.add("x")
    assert g.has("x")
    assert g.n_nodes == 1


def test_add_with_data():
    """add stores arbitrary data."""
    g = Graph(GraphInitParams(), logname="test_add_data")
    g.add("x", data={"color": "red", "hp": 100})
    assert g.get_node("x") == {"color": "red", "hp": 100}


def test_add_default_data_is_none():
    """Nodes without explicit data have None content."""
    g = Graph(GraphInitParams(), logname="test_node_default")
    g.add("a")
    assert g.get_node("a") is None


def test_add_duplicate():
    """Adding an existing node is a no-op (with warning)."""
    g = Graph(GraphInitParams(), logname="test_add_dup")
    g.add("x")
    g.add("x")
    assert g.n_nodes == 1


def test_rm():
    """Removing a node deletes it and its edges."""
    g = Graph(GraphInitParams(), logname="test_rm")
    g.add("a")
    g.add("b")
    g.connect("a", "b")
    g.rm("a")
    assert not g.has("a")
    assert g.neighbors("b") == {}


def test_rm_clears_data():
    """Removing a node also removes its data."""
    g = Graph(GraphInitParams(), logname="test_rm_data")
    g.add("x", data="important")
    g.rm("x")
    assert g.get_node("x") is None


def test_rm_missing():
    """Removing a non-existent node is a no-op."""
    g = Graph(GraphInitParams(), logname="test_rm_missing")
    g.rm("nope")  # should not raise
    assert g.n_nodes == 0


def test_has():
    """has returns correct bool."""
    g = Graph(GraphInitParams(), logname="test_has")
    g.add("a")
    assert g.has("a")
    assert not g.has("z")


def test_add_various_types():
    """Nodes can be any hashable type."""
    g = Graph(GraphInitParams(), logname="test_types")
    g.add(42)
    g.add("hello")
    g.add((1, 2, 3))
    assert g.n_nodes == 3
    assert g.has(42)
    assert g.has("hello")
    assert g.has((1, 2, 3))


def test_get_node():
    """get_node retrieves stored content."""
    g = Graph(GraphInitParams(), logname="test_data")
    g.add("a", data=[1, 2, 3])
    assert g.get_node("a") == [1, 2, 3]


def test_get_node_missing():
    """get_node returns None for non-existent node."""
    g = Graph(GraphInitParams(), logname="test_data_miss")
    assert g.get_node("nope") is None


def test_set_node():
    """set_node updates existing node content."""
    g = Graph(GraphInitParams(), logname="test_set_data")
    g.add("a", data="old")
    g.set_node("a", "new")
    assert g.get_node("a") == "new"


def test_set_node_missing():
    """set_node on non-existent node is a no-op."""
    g = Graph(GraphInitParams(), logname="test_set_data_miss")
    g.set_node("nope", "value")  # should not raise


def test_get_node_complex_objects():
    """Nodes can hold complex objects."""
    g = Graph(GraphInitParams(), logname="test_complex_node")

    class Piece:
        def __init__(self, name):
            self.name = name

    piece = Piece("knight")
    g.add("e4", data=piece)
    assert g.get_node("e4").name == "knight"


# EDGE OPERATIONS ##############################################################


def test_connect_undirected():
    """Undirected connect creates edges in both directions."""
    p = GraphInitParams(default_edge_data=1.0)
    g = Graph(p, logname="test_connect_undir")
    g.add("a")
    g.add("b")
    g.connect("a", "b")
    assert g.get_edge("a", "b") == 1.0
    assert g.get_edge("b", "a") == 1.0


def test_connect_directed():
    """Directed connect creates edge in one direction only."""
    p = GraphInitParams(directed=True, default_edge_data=1.0)
    g = Graph(p, logname="test_connect_dir")
    g.add("a")
    g.add("b")
    g.connect("a", "b")
    assert g.get_edge("a", "b") == 1.0
    assert g.get_edge("b", "a") is None


def test_connect_directed_override():
    """Per-call directed flag overrides graph default."""
    p = GraphInitParams(default_edge_data=1.0)
    g = Graph(p, logname="test_dir_override")
    g.add("a")
    g.add("b")
    g.connect("a", "b", directed=True)
    assert g.get_edge("a", "b") == 1.0
    assert g.get_edge("b", "a") is None


def test_connect_undirected_override():
    """Per-call directed=False overrides directed graph."""
    p = GraphInitParams(directed=True, default_edge_data=1.0)
    g = Graph(p, logname="test_undir_override")
    g.add("a")
    g.add("b")
    g.connect("a", "b", directed=False)
    assert g.get_edge("a", "b") == 1.0
    assert g.get_edge("b", "a") == 1.0


def test_connect_custom_data():
    """Custom edge data is stored."""
    g = Graph(GraphInitParams(), logname="test_edata")
    g.add("a")
    g.add("b")
    g.connect("a", "b", data=3.5)
    assert g.get_edge("a", "b") == 3.5
    assert g.get_edge("b", "a") == 3.5


def test_connect_dict_data():
    """Edges can carry dict data."""
    g = Graph(GraphInitParams(), logname="test_dict_edge")
    g.add("a")
    g.add("b")
    g.connect("a", "b", data={"weight": 5, "label": "road"})
    assert g.get_edge("a", "b") == {"weight": 5, "label": "road"}


def test_connect_string_data():
    """Edges can carry string data."""
    g = Graph(GraphInitParams(), logname="test_str_edge")
    g.add("a")
    g.add("b")
    g.connect("a", "b", data="highway")
    assert g.get_edge("a", "b") == "highway"


def test_connect_explicit_none_data():
    """Explicitly passing data=None stores None, not the default."""
    p = GraphInitParams(default_edge_data=99)
    g = Graph(p, logname="test_explicit_none")
    g.add("a")
    g.add("b")
    g.connect("a", "b", data=None)
    assert g.get_edge("a", "b") is None


def test_connect_missing_node():
    """Connecting to a non-existent node is a no-op."""
    g = Graph(GraphInitParams(), logname="test_connect_missing")
    g.add("a")
    g.connect("a", "b")  # b doesn't exist
    assert g.neighbors("a") == {}


def test_disconnect_undirected():
    """Undirected disconnect removes edges in both directions."""
    g = Graph(GraphInitParams(), logname="test_disconnect_undir")
    g.add("a")
    g.add("b")
    g.connect("a", "b", data=1.0)
    g.disconnect("a", "b")
    assert g.get_edge("a", "b") is None
    assert g.get_edge("b", "a") is None


def test_disconnect_directed():
    """Directed disconnect only removes a -> b."""
    g = Graph(GraphInitParams(), logname="test_disconnect_dir")
    g.add("a")
    g.add("b")
    g.connect("a", "b", data=1.0, directed=False)
    g.disconnect("a", "b", directed=True)
    assert g.get_edge("a", "b") is None
    assert g.get_edge("b", "a") == 1.0


def test_disconnect_missing_node():
    """Disconnecting non-existent nodes is a no-op."""
    g = Graph(GraphInitParams(), logname="test_disc_missing")
    g.disconnect("a", "b")  # neither exists


def test_disconnect_no_edge():
    """Disconnecting nodes with no edge is a no-op."""
    g = Graph(GraphInitParams(), logname="test_disc_no_edge")
    g.add("a")
    g.add("b")
    g.disconnect("a", "b")  # no edge, should not raise


def test_connect_overwrites_data():
    """Connecting again overwrites the edge data."""
    g = Graph(GraphInitParams(), logname="test_overwrite")
    g.add("a")
    g.add("b")
    g.connect("a", "b", data=1.0)
    g.connect("a", "b", data=5.0)
    assert g.get_edge("a", "b") == 5.0


def test_connect_default_data_is_none():
    """Without default_edge_data, edge data defaults to None."""
    g = Graph(GraphInitParams(), logname="test_default_edge")
    g.add("a")
    g.add("b")
    g.connect("a", "b")
    assert g.get_edge("a", "b") is None


def test_set_edge():
    """set_edge updates data on an existing edge."""
    g = Graph(GraphInitParams(), logname="test_set_edge")
    g.add("a")
    g.add("b")
    g.connect("a", "b", data=1.0)
    g.set_edge("a", "b", "updated")
    assert g.get_edge("a", "b") == "updated"
    # Undirected: reverse edge is NOT updated (set_edge is directional)
    assert g.get_edge("b", "a") == 1.0


def test_set_edge_missing():
    """set_edge on non-existent edge is a no-op."""
    g = Graph(GraphInitParams(), logname="test_set_edge_miss")
    g.add("a")
    g.add("b")
    g.set_edge("a", "b", "value")  # no edge, should not raise
    assert g.get_edge("a", "b") is None


def test_set_edge_no_node():
    """set_edge when nodes don't exist is a no-op."""
    g = Graph(GraphInitParams(), logname="test_set_edge_no_node")
    g.set_edge("x", "y", "value")  # should not raise


# QUERY OPERATIONS #############################################################


def test_neighbors():
    """neighbors returns dict of neighbor -> data."""
    p = GraphInitParams(default_edge_data=0)
    g = Graph(p, logname="test_neighbors")
    g.add("a")
    g.add("b")
    g.add("c")
    g.connect("a", "b", data=1.0)
    g.connect("a", "c", data=2.0)
    n = g.neighbors("a")
    assert n == {"b": 1.0, "c": 2.0}


def test_neighbors_where():
    """where predicate filters neighbors by edge data."""
    g = Graph(GraphInitParams(), logname="test_where")
    g.add("a")
    g.add("b")
    g.add("c")
    g.connect("a", "b", data=1.0)
    g.connect("a", "c", data=5.0)
    n = g.neighbors("a", where=lambda d: d <= 2.0)
    assert n == {"b": 1.0}


def test_neighbors_where_complex():
    """where predicate works with complex edge data."""
    g = Graph(GraphInitParams(), logname="test_where_complex")
    g.add("a")
    g.add("b")
    g.add("c")
    g.connect("a", "b", data={"type": "road", "cost": 1})
    g.connect("a", "c", data={"type": "river", "cost": 5})
    roads = g.neighbors("a", where=lambda d: d["type"] == "road")
    assert set(roads.keys()) == {"b"}


def test_neighbors_missing_node():
    """neighbors on non-existent node returns empty dict."""
    g = Graph(GraphInitParams(), logname="test_neighbors_missing")
    assert g.neighbors("nope") == {}


def test_get_edge_no_edge():
    """get_edge returns None when no edge exists."""
    g = Graph(GraphInitParams(), logname="test_edata_no")
    g.add("a")
    g.add("b")
    assert g.get_edge("a", "b") is None


def test_get_edge_no_node():
    """get_edge returns None when source node doesn't exist."""
    g = Graph(GraphInitParams(), logname="test_edata_no_node")
    assert g.get_edge("x", "y") is None


def test_degree():
    """degree returns outgoing edge count."""
    g = Graph(GraphInitParams(), logname="test_degree")
    g.add("a")
    g.add("b")
    g.add("c")
    g.connect("a", "b", data=1)
    g.connect("a", "c", data=1)
    assert g.degree("a") == 2


def test_degree_missing():
    """degree of non-existent node is 0."""
    g = Graph(GraphInitParams(), logname="test_degree_miss")
    assert g.degree("x") == 0


def test_degree_directed():
    """In a directed graph, degree only counts outgoing."""
    p = GraphInitParams(directed=True, default_edge_data=1)
    g = Graph(p, logname="test_degree_dir")
    g.add("a")
    g.add("b")
    g.connect("a", "b")
    assert g.degree("a") == 1
    assert g.degree("b") == 0


# ITERATION ####################################################################


def test_edges():
    """edges yields all directed edge tuples."""
    g = Graph(GraphInitParams(), logname="test_edges")
    g.add("a")
    g.add("b")
    g.connect("a", "b", data=2.0)
    result = list(g.edges())
    # Undirected: a->b and b->a
    assert ("a", "b", 2.0) in result
    assert ("b", "a", 2.0) in result
    assert len(result) == 2


def test_edges_directed():
    """edges on directed graph yields one-way edges."""
    p = GraphInitParams(directed=True)
    g = Graph(p, logname="test_edges_dir")
    g.add("a")
    g.add("b")
    g.connect("a", "b", data=1.0)
    result = list(g.edges())
    assert result == [("a", "b", 1.0)]


def test_edges_empty():
    """edges on empty graph yields nothing."""
    g = Graph(GraphInitParams(), logname="test_edges_empty")
    assert list(g.edges()) == []


# GRID FACTORY #################################################################


def test_grid_1d():
    """1D grid: linear chain."""
    g = Graph.grid((5,), logname="test_grid_1d")
    assert g.n_nodes == 5
    assert g.degree((2,)) == 2
    assert g.degree((0,)) == 1
    assert g.degree((4,)) == 1


def test_grid_2d():
    """2D grid: standard rectangle."""
    g = Graph.grid((3, 4), logname="test_grid_2d")
    assert g.n_nodes == 12
    assert g.degree((0, 0)) == 2
    assert g.degree((0, 1)) == 3
    assert g.degree((1, 1)) == 4


def test_grid_3d():
    """3D grid works."""
    g = Graph.grid((2, 2, 2), logname="test_grid_3d")
    assert g.n_nodes == 8
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
    assert g.degree((0, 0)) == 3


def test_grid_1d_wrap():
    """1D wrapped grid: ring topology."""
    g = Graph.grid((5,), wrap=(True,), logname="test_grid_ring")
    for node in g.nodes:
        assert g.degree(node) == 2
    assert g.get_edge((0,), (4,)) == 1.0
    assert g.get_edge((4,), (0,)) == 1.0


def test_grid_custom_edge_data():
    """Grid edges use the specified data."""
    g = Graph.grid((2, 2), edge_data=3.0, logname="test_grid_data")
    assert g.get_edge((0, 0), (0, 1)) == 3.0


def test_grid_non_numeric_edge_data():
    """Grid edges can carry non-numeric data."""
    g = Graph.grid((2, 2), edge_data="path", logname="test_grid_str")
    assert g.get_edge((0, 0), (0, 1)) == "path"


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
    assert g.degree((0,)) == 0


def test_grid_2x1_wrapped():
    """2x1 wrapped: two nodes connected, wrap connects same pair."""
    g = Graph.grid((2,), wrap=(True,), logname="test_grid_2x1_wrap")
    assert g.n_nodes == 2
    assert g.get_edge((0,), (1,)) == 1.0
    assert g.get_edge((1,), (0,)) == 1.0
    assert g.degree((0,)) == 1


# COMPLEX SCENARIOS ############################################################


def test_rm_cleans_all_edges():
    """Removing a highly-connected node cleans all inbound edges."""
    g = Graph(GraphInitParams(), logname="test_rm_hub")
    g.add("hub")
    g.add("a")
    g.add("b")
    g.add("c")
    g.connect("hub", "a", data=1)
    g.connect("hub", "b", data=1)
    g.connect("hub", "c", data=1)
    g.rm("hub")
    assert g.neighbors("a") == {}
    assert g.neighbors("b") == {}
    assert g.neighbors("c") == {}


def test_self_loop():
    """A node can connect to itself."""
    g = Graph(GraphInitParams(), logname="test_self_loop")
    g.add("a")
    g.connect("a", "a", data=1)
    assert g.get_edge("a", "a") is not None
    assert g.degree("a") == 1


def test_nodes_immutable():
    """nodes property returns a frozenset (immutable)."""
    g = Graph(GraphInitParams(), logname="test_frozen")
    g.add("a")
    ns = g.nodes
    assert isinstance(ns, frozenset)


def test_neighbors_returns_copy():
    """neighbors returns a copy, not a reference to internal state."""
    g = Graph(GraphInitParams(), logname="test_nbr_copy")
    g.add("a")
    g.add("b")
    g.connect("a", "b", data=1.0)
    n = g.neighbors("a")
    n["c"] = 99.0
    assert "c" not in g.neighbors("a")


def test_where_boundary():
    """where predicate at boundary: equal value is caller's choice."""
    g = Graph(GraphInitParams(), logname="test_boundary")
    g.add("a")
    g.add("b")
    g.add("c")
    g.connect("a", "b", data=2.0)
    g.connect("a", "c", data=3.0)
    n = g.neighbors("a", where=lambda d: d <= 2.0)
    assert "b" in n
    assert "c" not in n


def test_zero_data_edge():
    """Edges with data 0 are valid and distinguishable from None."""
    g = Graph(GraphInitParams(), logname="test_zero_data")
    g.add("a")
    g.add("b")
    g.connect("a", "b", data=0)
    assert g.get_edge("a", "b") == 0
    assert g.get_edge("a", "b") is not None


def test_where_with_none_data():
    """where predicate can filter edges with None data."""
    g = Graph(GraphInitParams(), logname="test_where_none")
    g.add("a")
    g.add("b")
    g.add("c")
    g.connect("a", "b", data="x")
    g.connect("a", "c")  # None data
    n = g.neighbors("a", where=lambda d: d is not None)
    assert set(n.keys()) == {"b"}
