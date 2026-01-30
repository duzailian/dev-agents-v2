import os
from pathlib import Path
from typing import Dict, List, Optional
from src.models.code import CodeAnalysis, CodeMetrics, CodeLocation, CodeIssue, IssueType, IssueSeverity

try:
    from tree_sitter import Language, Parser, Node
except ImportError:
    Language = None
    Parser = None
    Node = None

class TreeSitterCodeParser:
    """
    Parser for C/C++ code using tree-sitter.

    This class handles parsing of source files to extract metrics and structure.
    It requires tree-sitter language libraries to be compiled and available.
    """

    def __init__(self, build_dir: str = "build", vendor_dir: str = "vendor"):
        """
        Initialize the parser.

        Args:
            build_dir: Directory containing the compiled language libraries (languages.so/dll)
            vendor_dir: Directory containing tree-sitter grammar repositories
        """
        self.build_dir = build_dir
        self.vendor_dir = vendor_dir

        # Determine library extension based on OS
        lib_ext = "dll" if os.name == "nt" else "so"
        self.lib_file = os.path.join(build_dir, f"languages.{lib_ext}")

        self.languages: Dict[str, Language] = {}
        self.parser: Optional[Parser] = None

        if Parser:
            self.parser = Parser()
            self._initialize_languages()

    def _initialize_languages(self):
        """Initialize tree-sitter languages."""

        # Mapping extension to language name
        self.ext_map = {
            '.c': 'c',
            '.h': 'c',
            '.cpp': 'cpp',
            '.hpp': 'cpp',
            '.cc': 'cpp',
            '.cxx': 'cpp',
            '.hh': 'cpp'
        }

        # Check if library exists
        if not os.path.exists(self.lib_file):
            # We don't raise an error here to allow the parser to work in "text-only" mode
            # if the binaries aren't built yet.
            return

        try:
            # Attempt to load C
            self.languages['c'] = Language(self.lib_file, 'c')
            # Attempt to load C++
            self.languages['cpp'] = Language(self.lib_file, 'cpp')
        except Exception as e:
            # Log error but don't crash
            print(f"Warning: Failed to load tree-sitter languages: {e}")

    def parse_file(self, file_path: str) -> CodeAnalysis:
        """
        Parse a file and return a CodeAnalysis object.

        Args:
            file_path: Absolute path to the file to parse

        Returns:
            CodeAnalysis object populated with metrics and issues
        """
        path = Path(file_path)
        if not path.exists():
            # If file doesn't exist, return empty analysis with error?
            # Or raise? The requirements say "Handle errors gracefully".
            # Returning an object with an error issue seems appropriate.
            return CodeAnalysis(
                target_files=[file_path],
                issues=[CodeIssue(
                    title="File not found",
                    description=f"File does not exist: {file_path}",
                    severity=IssueSeverity.CRITICAL,
                    issue_type=IssueType.UNKNOWN
                )]
            )

        # Basic file stats
        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except Exception as e:
            return CodeAnalysis(
                target_files=[file_path],
                issues=[CodeIssue(
                    title="Read Error",
                    description=str(e),
                    severity=IssueSeverity.CRITICAL,
                    issue_type=IssueType.UNKNOWN
                )]
            )

        lines = content.splitlines()
        loc = len(lines)

        # Initialize metrics
        metrics = CodeMetrics(
            lines_of_code=loc,
            function_count=0,
            class_count=0,
            cyclomatic_complexity=0, # Placeholder
            cognitive_complexity=0   # Placeholder
        )

        analysis = CodeAnalysis(
            target_files=[file_path],
            metrics=metrics,
            issues=[]
        )

        # If parser setup failed or no suitable language, return basic metrics
        if not self.parser or not self.languages:
            return analysis

        # Determine language
        ext = path.suffix.lower()
        lang_name = self.ext_map.get(ext)

        if not lang_name or lang_name not in self.languages:
            return analysis

        # Parse
        lang = self.languages[lang_name]
        self.parser.set_language(lang)

        try:
            # Tree-sitter 0.21.x parse returns a Tree
            tree = self.parser.parse(bytes(content, "utf8"))
            root_node = tree.root_node

            # Analyze tree structure
            self._analyze_tree(root_node, metrics, lang_name)

            # Check for syntax errors
            if root_node.has_error:
                self._find_errors(root_node, analysis, file_path)

        except Exception as e:
            analysis.issues.append(CodeIssue(
                title="Parsing Error",
                description=str(e),
                severity=IssueSeverity.HIGH,
                issue_type=IssueType.UNKNOWN
            ))

        return analysis

    def _analyze_tree(self, node: Node, metrics: CodeMetrics, lang_name: str):
        """Recursively analyze the tree to update metrics."""

        node_type = node.type

        # Function definitions
        if node_type == 'function_definition':
            metrics.function_count += 1

        # C++ specific
        if lang_name == 'cpp':
            if node_type in ['class_specifier', 'struct_specifier']:
                metrics.class_count += 1

        # Traverse children
        for child in node.children:
            self._analyze_tree(child, metrics, lang_name)

    def _find_errors(self, node: Node, analysis: CodeAnalysis, file_path: str):
        """Find syntax errors in the tree."""
        if node.type == 'ERROR':
            # Create an issue
            issue = CodeIssue(
                issue_type=IssueType.COMPILATION_ERROR,
                severity=IssueSeverity.HIGH,
                title="Syntax Error",
                description=f"Syntax error found near line {node.start_point[0]+1}",
                location=CodeLocation(
                    file_path=file_path,
                    line_start=node.start_point[0]+1,
                    line_end=node.end_point[0]+1,
                    column_start=node.start_point[1],
                    column_end=node.end_point[1]
                )
            )
            analysis.issues.append(issue)
            # Avoid too many errors from the same subtree
            return

        for child in node.children:
            self._find_errors(child, analysis, file_path)

    def build_languages(self):
        """
        Helper to build languages if needed.
        Requires 'tree-sitter-c' and 'tree-sitter-cpp' in the vendor directory.
        """
        if not Language:
            print("Tree-sitter module not loaded.")
            return

        # Check for vendor directories
        c_path = os.path.join(self.vendor_dir, 'tree-sitter-c')
        cpp_path = os.path.join(self.vendor_dir, 'tree-sitter-cpp')

        if not os.path.exists(c_path) or not os.path.exists(cpp_path):
            print(f"Language repositories not found in {self.vendor_dir}. Please clone tree-sitter-c and tree-sitter-cpp.")
            return

        os.makedirs(self.build_dir, exist_ok=True)
        try:
            Language.build_library(
                self.lib_file,
                [c_path, cpp_path]
            )
            print(f"Built languages to {self.lib_file}")
        except Exception as e:
            print(f"Failed to build languages: {e}")
