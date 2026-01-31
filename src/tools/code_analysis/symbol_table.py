from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from src.models.code import Symbol, Location

class SymbolTable:
    """
    Symbol Table implementation for managing code symbols and scopes.

    Attributes:
        symbols (Dict[str, List[Symbol]]): Map of symbol name to list of Symbol definitions (to handle shadowing/overloading)
        scopes (List[str]): Stack of current scope names
    """

    def __init__(self):
        self.symbols: Dict[str, List[Symbol]] = {}
        self.scopes: List[str] = ["global"]

    def enter_scope(self, scope_name: str):
        """Enter a new scope."""
        self.scopes.append(scope_name)

    def exit_scope(self):
        """Exit the current scope."""
        if len(self.scopes) > 1:
            self.scopes.pop()

    def get_current_scope(self) -> str:
        """Get the fully qualified current scope name."""
        return "::".join(self.scopes)

    def add_symbol(self, name: str, kind: str, location: Location, type_info: Optional[str] = None):
        """
        Add a symbol to the table in the current scope.

        Args:
            name: Symbol name
            kind: Symbol kind ("function", "variable", "type", "macro")
            location: Source location
            type_info: Optional type information
        """
        scope = self.get_current_scope()
        symbol = Symbol(
            name=name,
            kind=kind,
            location=location,
            scope=scope,
            type_info=type_info
        )

        if name not in self.symbols:
            self.symbols[name] = []
        self.symbols[name].append(symbol)

    def lookup(self, name: str, scope: Optional[str] = None) -> Optional[Symbol]:
        """
        Look up a symbol by name.

        Args:
            name: Symbol name
            scope: Optional specific scope to search in. If None, searches closest to current scope.

        Returns:
            Symbol if found, None otherwise.
        """
        if name not in self.symbols:
            return None

        candidates = self.symbols[name]

        if scope:
            # Exact scope match
            for sym in candidates:
                if sym.scope == scope:
                    return sym
            return None

        # Scope resolution (simplistic: prefer longest matching suffix with current scope)
        # In a real compiler, we'd walk up the scope stack.
        current = self.get_current_scope()
        best_match = None
        best_score = -1

        for sym in candidates:
            # Simple heuristic: how much of the scope prefix matches?
            # actually for C/C++, we usually look in current scope, then parent, etc.

            # Check if symbol scope is a prefix of current scope (or equal)
            # OR if symbol is global

            if sym.scope == "global":
                score = 0
            elif current.startswith(sym.scope):
                score = len(sym.scope)
            else:
                continue

            if score > best_score:
                best_score = score
                best_match = sym

        return best_match

    def get_symbols_by_scope(self, scope: str) -> List[Symbol]:
        """Get all symbols defined in a specific scope."""
        result = []
        for sym_list in self.symbols.values():
            for sym in sym_list:
                if sym.scope == scope:
                    result.append(sym)
        return result

    def clear(self):
        """Clear the symbol table."""
        self.symbols.clear()
        self.scopes = ["global"]
