"""
Code Analysis Module

Provides code analysis capabilities for C/C++ source code:
- AST parsing with Tree-sitter
- Symbol table construction
- Call graph analysis
- Code metrics calculation
"""

from .analyzer import CodeAnalyzer, AnalyzerConfig
from .parser import TreeSitterParser
from .symbol_table import SymbolTable
from .call_graph import CallGraph
from .static_analyzers import ClangTidyAnalyzer, CppcheckAnalyzer

__all__ = [
    "CodeAnalyzer",
    "AnalyzerConfig",
    "TreeSitterParser",
    "SymbolTable",
    "CallGraph",
    "ClangTidyAnalyzer",
    "CppcheckAnalyzer",
]
