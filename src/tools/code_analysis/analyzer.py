"""
Code Analyzer Module

This module provides the main code analysis engine that orchestrates:
1. Parsing using TreeSitterParser
2. Symbol Table construction
3. Call Graph generation
4. Static Analysis integration
5. AI-based code understanding

Implementation based on docs/DETAILED_DESIGN_V2.md
"""

import asyncio
import logging
import os
from typing import List, Optional, Dict, Any, Union
from pathlib import Path
from datetime import datetime

# Import data models
from src.models.code import (
    AnalysisReport,
    FileAnalysis,
    Issue,
    Location,
    CodeMetrics,
    FunctionNode,
    AnalyzerConfig,
    AnalysisType,
    DependencyGraph,
    Symbol
)

# Import components
from src.tools.code_analysis.parser import TreeSitterParser
from src.tools.code_analysis.symbol_table import SymbolTable
from src.tools.code_analysis.call_graph import CallGraph

logger = logging.getLogger(__name__)

class LegacyStaticAnalyzerAdapter:
    """Adapter for legacy static analyzers to the new Issue format."""

    def __init__(self, legacy_tool):
        self.legacy_tool = legacy_tool

    async def analyze(self, file_path: str) -> List[Issue]:
        # Assume legacy tool returns list of dicts with title, description, severity
        legacy_issues = await self.legacy_tool.analyze(file_path)
        issues = []
        for li in legacy_issues:
            issues.append(Issue(
                rule_id="legacy_rule",
                severity=li.get('severity', 'info'),
                message=f"{li.get('title', 'Issue')}: {li.get('description', '')}",
                location=Location(file_path, 0, 0) # Location might be missing in legacy
            ))
        return issues

class CodeAnalyzer:
    """
    Code Analysis Engine Main Class.

    Orchestrates the analysis process for C/C++ code.
    """

    def __init__(self, config: AnalyzerConfig):
        """
        Initialize the analyzer.

        Args:
            config: Analyzer configuration
        """
        self.config = config
        self.parser = TreeSitterParser() # Initialize default parser
        self.symbol_table = SymbolTable()
        self.call_graph = CallGraph()
        self.static_analyzers = [] # Placeholder for future integrations
        self.llm_client = None # Placeholder for LLM client
        self._cache = {} if config.enable_caching else None

    async def analyze_files(
        self,
        file_paths: List[str],
        analysis_type: AnalysisType = AnalysisType.FULL
    ) -> AnalysisReport:
        """
        Analyze multiple files.

        Args:
            file_paths: List of file paths to analyze
            analysis_type: Type of analysis to perform

        Returns:
            AnalysisReport: Comprehensive analysis report
        """
        task_id = f"analysis_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        file_analyses: List[FileAnalysis] = []
        all_issues: List[Issue] = []

        # 1. Analyze each file
        for file_path in file_paths:
            try:
                # Basic analysis (parsing, metrics, symbols)
                file_analysis = await self.analyze_single_file(file_path)
                file_analyses.append(file_analysis)
                all_issues.extend(file_analysis.issues)

                # Update global symbol table and call graph
                self._update_global_structures(file_analysis)

            except Exception as e:
                logger.error(f"Failed to analyze {file_path}: {e}")
                # Create a placeholder analysis with error
                error_issue = Issue(
                    rule_id="analysis_error",
                    severity="error",
                    message=str(e),
                    location=Location(file_path, 0, 0)
                )
                file_analyses.append(FileAnalysis(
                    file_path=file_path,
                    language="unknown",
                    issues=[error_issue],
                    metrics=CodeMetrics(0,0,0,0,0,0), # Empty metrics
                    functions=[],
                    symbols=[],
                    includes=[],
                    ast_hash=""
                ))
                all_issues.append(error_issue)

        # 2. Run Static Analysis (if configured and requested)
        if analysis_type in [AnalysisType.STATIC, AnalysisType.FULL] and self.static_analyzers:
            static_issues = await self.run_static_analysis(file_paths)
            all_issues.extend(static_issues)

        # 3. AI Analysis (if configured and requested)
        # This is a placeholder for where AI analysis would hook in
        if analysis_type in [AnalysisType.AI, AnalysisType.FULL] and self.llm_client:
             ai_issues = await self.run_ai_analysis(file_paths)
             all_issues.extend(ai_issues)

        # 4. Build Dependency Graph
        dependency_graph = self._build_dependency_graph(file_analyses)

        # 5. Generate Summary
        summary = self._generate_summary(all_issues, len(file_paths))

        return AnalysisReport(
            task_id=task_id,
            timestamp=datetime.utcnow().isoformat(),
            files_analyzed=file_paths,
            file_analyses=file_analyses,
            dependency_graph=dependency_graph,
            call_graph=self.call_graph.to_dict(),
            total_issues=len(all_issues),
            issues_by_severity=self._count_issues_by_severity(all_issues),
            summary=summary,
            suggestions=[]
        )

    async def run_static_analysis(self, file_paths: List[str]) -> List[Issue]:
        """
        Run configured static analysis tools.

        Args:
            file_paths: Files to analyze

        Returns:
            List[Issue]: Detected issues
        """
        issues = []
        for tool in self.static_analyzers:
            for file_path in file_paths:
                 try:
                     # Check if tool supports async, otherwise run in executor?
                     # For now assuming async interface as per tests
                     if asyncio.iscoroutinefunction(tool.analyze):
                         tool_issues = await tool.analyze(file_path)
                     else:
                         tool_issues = tool.analyze(file_path)

                     if tool_issues:
                         issues.extend(tool_issues)
                 except Exception as e:
                     logger.error(f"Static analyzer failed on {file_path}: {e}")
                     # Optionally add an issue about the tool failure
                     issues.append(Issue(
                         rule_id="tool_error",
                         severity="error",
                         message=f"Static analyzer failed: {e}",
                         location=Location(file_path, 0, 0)
                     ))
        return issues

    async def run_ai_analysis(self, file_paths: List[str]) -> List[Issue]:
        """Run AI analysis on files."""
        # Simple implementation that calls the LLM client's analyze method
        # This assumes the LLM client has an 'analyze' method compatible with our needs
        issues = []
        if self.llm_client:
             for file_path in file_paths:
                 try:
                     if hasattr(self.llm_client, 'analyze'):
                         if asyncio.iscoroutinefunction(self.llm_client.analyze):
                             tool_issues = await self.llm_client.analyze(file_path=file_path)
                         else:
                             tool_issues = self.llm_client.analyze(file_path=file_path)

                         if tool_issues:
                             issues.extend(tool_issues)
                 except Exception as e:
                     logger.error(f"AI analyzer failed on {file_path}: {e}")
        return issues


    async def analyze_file(self, file_path: str) -> AnalysisReport:
        """
        Analyze a single file (Convenience wrapper).

        Args:
            file_path: Path to the file

        Returns:
            AnalysisReport: Analysis report for the file
        """
        return await self.analyze_files([file_path])

    async def analyze_directory(self, directory: str) -> Dict[str, Any]:
        """
        Analyze all supported files in a directory.

        Args:
            directory: Directory path

        Returns:
            Dict[str, Any]: Map of filename to analysis results
        """
        path = Path(directory)
        if not path.exists():
             # Return empty or let analyze_files handle empty list?
             # Tests expect a dict result, let's assume analyze_files logic but returned differently?
             # Actually, analyze_files returns AnalysisReport.
             # The test expects a dict where keys contain filenames.
             pass

        files = []
        for root, _, filenames in os.walk(directory):
            for f in filenames:
                if f.endswith(('.c', '.h', '.cpp', '.hpp', '.cc', '.cxx')):
                    files.append(os.path.join(root, f))

        report = await self.analyze_files(files)

        # Convert to dict format expected by tests/callers if needed,
        # or just return map of file_path -> FileAnalysis
        results = {}
        for fa in report.file_analyses:
            results[str(fa.file_path)] = fa

        return results

    def register_static_analyzer(self, tool):
        """Register a static analysis tool."""
        self.static_analyzers.append(tool)

    def set_ai_analyzer(self, tool):
        """Set the AI analyzer tool."""
        self.llm_client = tool

    # --- Internal Helpers ---

    def _update_global_structures(self, analysis: FileAnalysis):
        """Update global Symbol Table and Call Graph with file analysis results."""
        # Update Symbol Table
        for sym in analysis.symbols:
            self.symbol_table.add_symbol(sym.name, sym.kind, sym.location, sym.type_info)

        # Update Call Graph (requires extracting calls which we did in analyze_single_file)
        # We need to re-parse or pass calls data.
        # For now, let's assume we can re-extract or pass it if we modify FileAnalysis
        # But FileAnalysis doesn't store calls directly (it stores functions).

        # Let's re-extract calls quickly (inefficient but safe for now)
        # TODO: Add calls to FileAnalysis model or cache them
        with open(analysis.file_path, 'r', encoding='utf-8', errors='replace') as f:
            code = f.read()

        # We need to switch parser lang if needed
        # ... (skip strictly for brevity, assuming standard mix)

        calls = self.parser.extract_calls(code)

        # We need to know who is the caller.
        # extract_calls gives a list of calls, but doesn't explicitly link to caller function
        # The parser's extract_calls is simple.
        # To build a proper call graph, we need to traverse function bodies.

        # Improvement: Map calls to functions based on location ranges
        for call in calls:
            callee = call['callee']
            call_line = call['line']

            # Find caller
            caller = "global"
            for func in analysis.functions:
                if func.body_start <= 0: continue # No body info in some cases?
                # We need line numbers for functions, FunctionNode has location
                if (func.location.line <= call_line <= func.location.end_line):
                    caller = func.name
                    break

            self.call_graph.add_call(caller, callee, f"{analysis.file_path}:{call_line}")

    def _extract_includes(self, code: str) -> List[str]:
        """Extract #include statements."""
        includes = []
        for line in code.splitlines():
            line = line.strip()
            if line.startswith('#include'):
                # Extract content inside <...> or "..."
                parts = line.split(maxsplit=1)
                if len(parts) > 1:
                    includes.append(parts[1])
        return includes

    def _build_dependency_graph(self, analyses: List[FileAnalysis]) -> DependencyGraph:
        """Build dependency graph from multiple file analyses."""
        nodes = []
        edges = []
        include_map = {}

        for analysis in analyses:
            nodes.append(analysis.file_path)
            include_map[analysis.file_path] = analysis.includes

            for inc in analysis.includes:
                # Cleanup include string to get filename
                clean_inc = inc.strip('<">')

                # Try to find which analyzed file matches this include
                # Simple matching
                target = None
                for other in analyses:
                    if other.file_path.endswith(clean_inc):
                        target = other.file_path
                        break

                if target:
                    edges.append({"from": analysis.file_path, "to": target, "type": "include"})
                else:
                    # External dependency
                    if clean_inc not in nodes:
                        nodes.append(clean_inc)
                    edges.append({"from": analysis.file_path, "to": clean_inc, "type": "external_include"})

        return DependencyGraph(nodes=nodes, edges=edges, include_map=include_map)

    def _count_issues_by_severity(self, issues: List[Issue]) -> Dict[str, int]:
        counts = {}
        for issue in issues:
            severity = issue.severity.lower() if isinstance(issue.severity, str) else str(issue.severity)
            counts[severity] = counts.get(severity, 0) + 1
        return counts

    def _generate_summary(self, issues: List[Issue], file_count: int) -> str:
        if not issues:
            return f"Analyzed {file_count} files. No issues found."

        error_count = sum(1 for i in issues if str(i.severity).lower() in ['error', 'critical', 'high'])
        return f"Analyzed {file_count} files. Found {len(issues)} issues ({error_count} errors)."
