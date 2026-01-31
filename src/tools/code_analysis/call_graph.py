from typing import Dict, List, Set, Optional
from dataclasses import dataclass, field

@dataclass
class CallEdge:
    caller: str
    callee: str
    count: int = 1
    locations: List[str] = field(default_factory=list) # simplified location strings

class CallGraph:
    """
    Call Graph implementation for tracking function call relationships.

    Attributes:
        nodes (Set[str]): Set of function names (nodes)
        edges (List[CallEdge]): List of call edges
        _adjacency (Dict[str, List[str]]): Adjacency list for quick lookup
        _reverse_adjacency (Dict[str, List[str]]): Reverse adjacency list (called_by)
    """

    def __init__(self):
        self.nodes: Set[str] = set()
        self.edges: List[CallEdge] = []
        self._adjacency: Dict[str, List[str]] = {}
        self._reverse_adjacency: Dict[str, List[str]] = {}

    def add_node(self, function_name: str):
        """Add a function node to the graph."""
        self.nodes.add(function_name)
        if function_name not in self._adjacency:
            self._adjacency[function_name] = []
        if function_name not in self._reverse_adjacency:
            self._reverse_adjacency[function_name] = []

    def add_call(self, caller: str, callee: str, location: Optional[str] = None):
        """
        Add a call edge from caller to callee.

        Args:
            caller: Name of calling function
            callee: Name of called function
            location: Optional string representation of call location
        """
        self.add_node(caller)
        self.add_node(callee)

        # Check if edge exists
        existing_edge = None
        for edge in self.edges:
            if edge.caller == caller and edge.callee == callee:
                existing_edge = edge
                break

        if existing_edge:
            existing_edge.count += 1
            if location:
                existing_edge.locations.append(location)
        else:
            new_edge = CallEdge(caller=caller, callee=callee)
            if location:
                new_edge.locations.append(location)
            self.edges.append(new_edge)
            self._adjacency[caller].append(callee)
            self._reverse_adjacency[callee].append(caller)

    def get_callers(self, function_name: str) -> List[str]:
        """Get list of functions that call the specified function."""
        return self._reverse_adjacency.get(function_name, [])

    def get_callees(self, function_name: str) -> List[str]:
        """Get list of functions called by the specified function."""
        return self._adjacency.get(function_name, [])

    def get_edges(self) -> List[CallEdge]:
        """Get all edges."""
        return self.edges

    def to_dict(self) -> Dict[str, List[str]]:
        """Convert to dictionary representation (adjacency list)."""
        return self._adjacency

    def clear(self):
        """Clear the graph."""
        self.nodes.clear()
        self.edges.clear()
        self._adjacency.clear()
        self._reverse_adjacency.clear()
