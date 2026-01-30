import asyncio
import logging
from typing import List, Optional, Protocol, Dict, Any
from pathlib import Path

from src.models.code import CodeAnalysis, CodeIssue, CodeMetrics, IssueType, IssueSeverity
from src.tools.code_analysis.parser import TreeSitterCodeParser

logger = logging.getLogger(__name__)

class StaticAnalyzer(Protocol):
    """
    Protocol for static analysis tools.

    Any concrete static analyzer (like a wrapper for cppcheck or clang-tidy)
    should implement this interface.
    """

    async def analyze(self, file_path: str) -> List[CodeIssue]:
        """
        Analyze a file and return a list of issues.

        Args:
            file_path: Absolute path to the file to analyze.

        Returns:
            List of detected CodeIssues.
        """
        ...

class AIAnalyzer(Protocol):
    """
    Protocol for AI-based analysis tools.
    """
    async def analyze(self, file_path: str, context: CodeAnalysis) -> List[CodeIssue]:
        """
        Analyze code using AI/LLM.

        Args:
            file_path: Path to the file.
            context: Existing analysis context (metrics, AST info).

        Returns:
            List of AI-detected issues or suggestions.
        """
        ...

class CodeAnalyzer:
    """
    Main coordinator for code analysis.

    This class orchestrates the analysis process by:
    1. Parsing the code using TreeSitterCodeParser to get structural metrics.
    2. invoking registered StaticAnalyzer tools.
    3. invoking AI/RAG based analysis (placeholder).
    4. Aggregating all results into a single CodeAnalysis object.
    """

    def __init__(self, parser: Optional[TreeSitterCodeParser] = None):
        """
        Initialize the CodeAnalyzer.

        Args:
            parser: Optional instance of TreeSitterCodeParser.
                   If None, a default instance is created.
        """
        self.parser = parser or TreeSitterCodeParser()
        self.static_analyzers: List[StaticAnalyzer] = []
        self.ai_analyzer: Optional[AIAnalyzer] = None

    def register_static_analyzer(self, analyzer: StaticAnalyzer):
        """
        Register a static analysis tool.

        Args:
            analyzer: An object implementing the StaticAnalyzer protocol.
        """
        self.static_analyzers.append(analyzer)

    def set_ai_analyzer(self, analyzer: AIAnalyzer):
        """
        Set the AI analyzer.

        Args:
            analyzer: An object implementing the AIAnalyzer protocol.
        """
        self.ai_analyzer = analyzer

    async def analyze_file(self, file_path: str) -> CodeAnalysis:
        """
        Perform comprehensive analysis on a single file.

        This method aggregates results from the parser, static analyzers,
        and AI analyzer.

        Args:
            file_path: Absolute path to the file.

        Returns:
            CodeAnalysis object containing all findings.
        """
        logger.info(f"Starting analysis for {file_path}")

        # 1. Parse file using Tree-sitter (Synchronous)
        # The parser handles file reading and basic metric extraction.
        try:
            # We run this directly. In a high-load async environment,
            # this could be offloaded to a thread pool if parsing is slow.
            base_analysis = self.parser.parse_file(file_path)
        except Exception as e:
            logger.error(f"Parser failed for {file_path}: {e}")
            return CodeAnalysis(
                target_files=[file_path],
                issues=[CodeIssue(
                    title="Analysis Orchestration Error",
                    description=f"Parser failed: {str(e)}",
                    severity=IssueSeverity.CRITICAL,
                    issue_type=IssueType.UNKNOWN
                )]
            )

        # 2. Run Static Analyzers (Async)
        # We run all registered static analyzers in parallel.
        if self.static_analyzers:
            static_tasks = [
                analyzer.analyze(file_path) for analyzer in self.static_analyzers
            ]

            try:
                # gather returns a list of results (each result is a List[CodeIssue])
                results = await asyncio.gather(*static_tasks, return_exceptions=True)

                for res in results:
                    if isinstance(res, list):
                        base_analysis.issues.extend(res)
                    elif isinstance(res, Exception):
                        logger.error(f"Static analyzer failed: {res}")
                        base_analysis.issues.append(CodeIssue(
                            title="Static Analysis Tool Error",
                            description=str(res),
                            severity=IssueSeverity.HIGH,
                            issue_type=IssueType.UNKNOWN
                        ))
            except Exception as e:
                logger.error(f"Error executing static analyzers: {e}")

        # 3. AI Analysis (Placeholder integration)
        if self.ai_analyzer:
            try:
                ai_issues = await self.ai_analyzer.analyze(file_path, base_analysis)
                if ai_issues:
                    base_analysis.issues.extend(ai_issues)
            except Exception as e:
                logger.error(f"AI analyzer failed: {e}")
                # We don't fail the whole analysis if AI fails, just log it.

        return base_analysis

    async def analyze_directory(self, dir_path: str, recursive: bool = True) -> Dict[str, CodeAnalysis]:
        """
        Analyze all supported source files in a directory.

        Args:
            dir_path: Directory path.
            recursive: Whether to search recursively.

        Returns:
            Dictionary mapping file paths to their analysis results.
        """
        path = Path(dir_path)
        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {dir_path}")

        pattern = "**/*" if recursive else "*"
        # Filter for C/C++ files
        extensions = {'.c', '.h', '.cpp', '.hpp', '.cc', '.cxx'}

        tasks = []
        file_paths = []

        # Collect files
        for file_path in path.glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in extensions:
                str_path = str(file_path.absolute())
                file_paths.append(str_path)
                tasks.append(self.analyze_file(str_path))

        if not tasks:
            return {}

        # Run all file analyses in parallel
        results = await asyncio.gather(*tasks)

        return dict(zip(file_paths, results))
