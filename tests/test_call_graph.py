import pytest
from src.tools.code_analysis.call_graph import CallGraph

class TestCallGraph:
    def test_add_call(self):
        graph = CallGraph()
        graph.add_call("main", "func1", "main.c:10")

        assert "main" in graph.nodes
        assert "func1" in graph.nodes

        callees = graph.get_callees("main")
        assert "func1" in callees

        callers = graph.get_callers("func1")
        assert "main" in callers

    def test_multiple_calls(self):
        graph = CallGraph()
        graph.add_call("main", "func1")
        graph.add_call("main", "func2")
        graph.add_call("func1", "func3")

        assert len(graph.get_callees("main")) == 2
        assert len(graph.get_callers("func3")) == 1

    def test_edge_attributes(self):
        graph = CallGraph()
        graph.add_call("main", "func1", "loc1")
        graph.add_call("main", "func1", "loc2")

        edges = graph.get_edges()
        # Should merge into one edge with count 2
        assert len(edges) == 1
        assert edges[0].count == 2
        assert len(edges[0].locations) == 2
