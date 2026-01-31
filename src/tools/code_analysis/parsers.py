import os
from typing import List, Dict, Any, Optional
from tree_sitter import Language, Parser, Tree, Node, Query, QueryCursor
import tree_sitter_c as tsc
import tree_sitter_cpp as tscpp
from src.models.code import FunctionNode, Location

class TreeSitterParser:
    """Tree-sitter parser wrapper for C/C++"""

    LANGUAGE_MAP = {
        "c": "c",
        "cpp": "cpp",
        "c++": "cpp",
        "h": "c",  # Default .h to C, though could be C++
        "hpp": "cpp"
    }

    # C/C++ function definition query
    # Captures return type, name, parameters, and body
    FUNCTION_QUERY = """
    (function_definition
      type: (_) @return_type
      declarator: (function_declarator
        declarator: (identifier) @name
        parameters: (parameter_list) @params)
      body: (compound_statement) @body) @function
    """

    # Function call query
    CALL_QUERY = """
    (call_expression
      function: (identifier) @callee
      arguments: (argument_list) @args) @call
    """

    def __init__(self, language: str = "c"):
        """
        Initialize the parser for a specific language.

        Args:
            language: "c" or "cpp"
        """
        self.lang_name = self.LANGUAGE_MAP.get(language.lower())

        if self.lang_name == "c":
            self.language = Language(tsc.language())
        elif self.lang_name == "cpp":
            self.language = Language(tscpp.language())
        else:
            raise ValueError(f"Unsupported language: {language}")

        self.parser = Parser(self.language)

    def parse(self, code: str) -> Tree:
        """
        Parse source code into an AST.

        Args:
            code: Source code string

        Returns:
            Tree: Tree-sitter AST
        """
        return self.parser.parse(bytes(code, "utf8"))

    def query(self, tree: Tree, pattern: str) -> Dict[str, List[Node]]:
        """
        Execute a query pattern on the AST.

        Args:
            tree: AST to query
            pattern: S-expression query pattern

        Returns:
            Dict mapping capture names to lists of Nodes
        """
        query = Query(self.language, pattern)
        cursor = QueryCursor(query)
        captures = cursor.captures(tree.root_node)

        # organize captures by name
        results = {}
        for node, name in captures:
            if name not in results:
                results[name] = []
            results[name].append(node)

        return results

    def extract_functions(self, code: str, file_path: str = "") -> List[FunctionNode]:
        """
        Extract function definitions from code.

        Args:
            code: Source code
            file_path: Path to the file (for location info)

        Returns:
            List[FunctionNode]: Extracted functions
        """
        tree = self.parse(code)

        # We need to manually process captures to group them into functions
        # The simple query() method separates captures, losing the relationship between
        # return_type, name, and body of the SAME function.
        # So we iterate over matches instead.

        query = Query(self.language, self.FUNCTION_QUERY)
        cursor = QueryCursor(query)
        matches = cursor.matches(tree.root_node)

        functions = []

        for match in matches:
            # match consists of (pattern_index, {capture_name: [nodes]})
            # In new API, match might be Match object or tuple.
            # Based on debug output, let's assume standard behavior or dict.
            # Usually match is a tuple or object with captures.

            # Note: tree-sitter Python bindings vary.
            # If match is tuple: (pattern_index, capture_dict) where capture_dict = {name: [nodes]}

            captures = {}
            # Handle different match formats if needed, but assuming standard tuple for now
            if isinstance(match, tuple) and len(match) >= 2:
                 captures = match[1]
            elif hasattr(match, 'captures'):
                 # If it's an object with captures attribute
                 captures = match.captures
            else:
                 # Fallback/Debug
                 continue

            # Helper to get text from node
            def get_text(node: Node) -> str:
                return code[node.start_byte:node.end_byte]

            # Extract nodes based on capture names in the query
            name_node = captures.get('name', [None])[0]
            return_type_node = captures.get('return_type', [None])[0]
            params_node = captures.get('params', [None])[0]
            body_node = captures.get('body', [None])[0]
            function_node = captures.get('function', [None])[0] # The whole definition

            if not (name_node and function_node):
                continue

            # Location info
            loc = Location(
                file_path=file_path,
                line=function_node.start_point[0] + 1, # 1-based
                column=function_node.start_point[1] + 1,
                end_line=function_node.end_point[0] + 1,
                end_column=function_node.end_point[1] + 1
            )

            # Simple parameter parsing (just raw text for now, could be detailed)
            params_text = get_text(params_node) if params_node else ""
            # TODO: Better parameter parsing
            parameters = [{"raw": params_text}]

            func = FunctionNode(
                name=get_text(name_node),
                location=loc,
                return_type=get_text(return_type_node) if return_type_node else "void",
                parameters=parameters,
                body_start=body_node.start_byte if body_node else 0,
                body_end=body_node.end_byte if body_node else 0,
                docstring=None # TODO: Extract docstring preceding the function
            )

            functions.append(func)

        return functions

    def extract_calls(self, code: str) -> List[Dict[str, Any]]:
        """
        Extract function calls.

        Returns:
            List of dicts with 'callee', 'args', 'location'
        """
        tree = self.parse(code)
        query = Query(self.language, self.CALL_QUERY)
        cursor = QueryCursor(query)
        matches = cursor.matches(tree.root_node)

        calls = []
        for match in matches:
            captures = {}
            if isinstance(match, tuple) and len(match) >= 2:
                 captures = match[1]

            callee_node = captures.get('callee', [None])[0]
            args_node = captures.get('args', [None])[0]

            if not callee_node:
                continue

            calls.append({
                "callee": code[callee_node.start_byte:callee_node.end_byte],
                "args": code[args_node.start_byte:args_node.end_byte] if args_node else "",
                "line": callee_node.start_point[0] + 1
            })

        return calls
