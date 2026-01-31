import pytest
from src.tools.code_analysis.symbol_table import SymbolTable
from src.models.code import Location

class TestSymbolTable:
    def test_basic_operations(self):
        table = SymbolTable()
        loc = Location(file_path="test.c", line=1, column=1)

        table.add_symbol("func1", "function", loc, "void")
        sym = table.lookup("func1")

        assert sym is not None
        assert sym.name == "func1"
        assert sym.kind == "function"
        assert sym.scope == "global"

    def test_scope_management(self):
        table = SymbolTable()
        loc = Location(file_path="test.c", line=1, column=1)

        table.enter_scope("namespace1")
        table.add_symbol("var1", "variable", loc, "int")

        assert table.get_current_scope() == "global::namespace1"

        sym = table.lookup("var1")
        assert sym is not None
        assert sym.scope == "global::namespace1"

        table.exit_scope()
        assert table.get_current_scope() == "global"

        # Should still find it via scope rules or explicit scope if implemented
        # The current implementation has a simple heuristic, let's check basic lookup
        sym_lookup = table.lookup("var1")
        # Since we are in global, and var1 is in global::namespace1,
        # the heuristic might not find it unless we search specifically?
        # Let's check the current implementation logic:
        # lookup("var1") -> candidates found.
        # current scope "global". candidate scope "global::namespace1".
        # "global".startswith("global::namespace1") is False.
        # "global::namespace1".startswith("global") is True.
        # So "global" prefix match logic: current.startswith(sym.scope) is False.
        # Wait, the logic is: if current.startswith(sym.scope).
        # If I am in inner scope, I can see outer scope.
        # If I am in outer scope, I usually CANNOT see inner scope unless fully qualified.

        assert sym_lookup is None # Correct behavior for C++ (need qualification)

    def test_lookup_scopes(self):
        table = SymbolTable()
        loc = Location("test.c", 1, 1)

        table.add_symbol("global_var", "variable", loc, "int")

        table.enter_scope("func")
        table.add_symbol("local_var", "variable", loc, "int")

        # Should see global
        assert table.lookup("global_var") is not None

        # Should see local
        assert table.lookup("local_var") is not None

        table.exit_scope()

        # Global shouldn't see local
        assert table.lookup("local_var") is None
