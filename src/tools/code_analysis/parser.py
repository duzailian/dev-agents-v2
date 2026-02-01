import os
from typing import List, Dict, Any, Optional
from tree_sitter import Language, Parser, Tree, Node, Query
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
            self.language = Language(tsc.language(), 'c')
            self.parser = Parser(self.language)
        elif self.lang_name == "cpp":
            self.language = Language(tscpp.language(), 'cpp')
            self.parser = Parser(self.language)
        else:
            raise ValueError(f"Unsupported language: {language}")

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
        query = self.language.query(pattern)
        # Use query.matches() instead of deprecated query.captures()
        matches = query.matches(tree.root_node)

        results = {}
        for match in matches:
            # match is a tuple: (pattern_index, captures_dict)
            # captures_dict maps capture_name -> Node or list of Nodes
            if isinstance(match, tuple) and len(match) >= 2:
                captures = match[1]
                for name, node in captures.items():
                    if name not in results:
                        results[name] = []
                    if isinstance(node, list):
                        results[name].extend(node)
                    else:
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
        query = Query(self.language, self.FUNCTION_QUERY)
        matches = query.matches(tree.root_node)

        functions = []

        for match in matches:
            # match is a tuple: (pattern_index, captures_dict)
            # captures_dict maps capture_name -> Node or list of Nodes

            captures = {}
            if isinstance(match, tuple) and len(match) >= 2:
                 captures = match[1]
            else:
                 continue

            # Helper to safely get a single node
            def get_node(name):
                val = captures.get(name)
                if isinstance(val, list):
                    return val[0] if val else None
                return val

            # Helper to get text from node
            def get_text(node: Node) -> str:
                return code[node.start_byte:node.end_byte]

            name_node = get_node('name')
            return_type_node = get_node('return_type')
            params_node = get_node('params')
            body_node = get_node('body')
            function_node = get_node('function')

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

            # Simple parameter parsing
            params_text = get_text(params_node) if params_node else ""
            parameters = [{"raw": params_text}]

            func = FunctionNode(
                name=get_text(name_node),
                location=loc,
                return_type=get_text(return_type_node) if return_type_node else "void",
                parameters=parameters,
                body_start=body_node.start_byte if body_node else 0,
                body_end=body_node.end_byte if body_node else 0,
                docstring=None
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
        matches = query.matches(tree.root_node)

        calls = []
        for match in matches:
            captures = {}
            if isinstance(match, tuple) and len(match) >= 2:
                 captures = match[1]

            # Helper to safely get a single node
            def get_node(name):
                val = captures.get(name)
                if isinstance(val, list):
                    return val[0] if val else None
                return val

            callee_node = get_node('callee')
            args_node = get_node('args')

            if not callee_node:
                continue

            calls.append({
                "callee": code[callee_node.start_byte:callee_node.end_byte],
                "args": code[args_node.start_byte:args_node.end_byte] if args_node else "",
                "line": callee_node.start_point[0] + 1
            })

        return calls
