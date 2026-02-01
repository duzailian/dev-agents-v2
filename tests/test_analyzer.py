"""
Tests for CodeAnalyzer module.

These tests verify the new API (AnalysisReport, Issue, etc.) works correctly.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from src.tools.code_analysis.analyzer import CodeAnalyzer, LegacyStaticAnalyzerAdapter
from src.models.code import Issue, Location, AnalysisReport, AnalyzerConfig


@pytest.fixture
def analyzer_config():
    return AnalyzerConfig()

@pytest.mark.asyncio
async def test_analyzer_basic_flow(tmp_path, analyzer_config):
    """Test basic analysis flow with real file."""
    # Create a real test file
    test_file = tmp_path / "test.c"
    test_file.write_text("int main() { return 0; }")

    analyzer = CodeAnalyzer(analyzer_config)

    result = await analyzer.analyze_file(str(test_file))

    assert isinstance(result, AnalysisReport)
    assert len(result.files_analyzed) == 1
    assert result.files_analyzed[0] == str(test_file)


@pytest.mark.asyncio
async def test_analyzer_with_static_tool(tmp_path, analyzer_config):
    """Test analyzer with a registered static analyzer."""
    # Create a real test file
    test_file = tmp_path / "test.c"
    test_file.write_text("int main() { return 0; }")

    analyzer = CodeAnalyzer(analyzer_config)

    # Create a mock static analyzer that returns new Issue objects
    mock_tool = MagicMock()
    mock_tool.analyze = AsyncMock(return_value=[
        Issue(
            rule_id="test-rule",
            severity="warning",
            message="Static Bug found",
            location=Location(file_path=str(test_file), line=10, column=5)
        )
    ])

    analyzer.register_static_analyzer(mock_tool)

    result = await analyzer.analyze_file(str(test_file))

    mock_tool.analyze.assert_called_once_with(str(test_file))
    assert result.total_issues >= 1


@pytest.mark.asyncio
async def test_analyzer_with_ai_tool(tmp_path, analyzer_config):
    """Test analyzer with AI tool."""
    # Create a real test file
    test_file = tmp_path / "test.c"
    test_file.write_text("int main() { return 0; }")

    analyzer = CodeAnalyzer(analyzer_config)

    mock_ai = MagicMock()
    mock_ai.analyze = AsyncMock(return_value=[
        Issue(
            rule_id="ai-suggestion",
            severity="info",
            message="AI Suggestion",
            location=Location(file_path=str(test_file), line=1, column=1)
        )
    ])

    analyzer.set_ai_analyzer(mock_ai)

    result = await analyzer.analyze_file(str(test_file))

    mock_ai.analyze.assert_called_once()
    assert result.total_issues >= 1


@pytest.mark.asyncio
async def test_analyzer_exception_handling(tmp_path, analyzer_config):
    """Test that exception in one tool doesn't crash the whole analysis."""
    # Create a real test file
    test_file = tmp_path / "test.c"
    test_file.write_text("int main() { return 0; }")

    analyzer = CodeAnalyzer(analyzer_config)

    # Only register the bad tool to test exception handling
    mock_tool_bad = MagicMock()
    mock_tool_bad.analyze = AsyncMock(side_effect=Exception("Tool crashed"))

    analyzer.register_static_analyzer(mock_tool_bad)

    result = await analyzer.analyze_file(str(test_file))

    # Should have 1 issue from the error report (not crash)
    assert result.total_issues >= 1

    # Check that we have the error report
    messages = []
    for file_analysis in result.file_analyses:
        for issue in file_analysis.issues:
            messages.append(issue.message)

    # Should have the error report for the crashed tool
    has_error = any("Tool crashed" in msg for msg in messages)
    assert has_error, f"Expected 'Tool crashed' in messages: {messages}"


@pytest.mark.asyncio
async def test_analyze_directory(tmp_path, analyzer_config):
    """Test directory analysis."""
    # Setup a fake directory structure
    d = tmp_path / "src"
    d.mkdir()
    (d / "a.c").write_text("int a() { return 1; }")
    (d / "b.h").write_text("int b();")
    (d / "readme.txt").write_text("text")  # Should be ignored

    analyzer = CodeAnalyzer(analyzer_config)

    results = await analyzer.analyze_directory(str(d))

    assert len(results) == 2

    # Check that keys contain the filenames
    keys = list(results.keys())
    assert any("a.c" in k for k in keys)
    assert any("b.h" in k for k in keys)
    assert not any("readme.txt" in k for k in keys)


@pytest.mark.asyncio
async def test_legacy_api_compatibility(tmp_path, analyzer_config):
    """Test that legacy API still works through adapter."""
    # Create a real test file
    test_file = tmp_path / "test.c"
    test_file.write_text("int main() { return 0; }")

    analyzer = CodeAnalyzer(analyzer_config)

    # Create a mock legacy static analyzer
    class LegacyAnalyzer:
        async def analyze(self, file_path: str):
            # Returns old format
            return [{
                'title': 'Legacy Bug',
                'description': 'Found via legacy analyzer',
                'severity': 'high'
            }]

    # Register legacy analyzer through adapter
    legacy = LegacyAnalyzer()
    adapter = LegacyStaticAnalyzerAdapter(legacy)
    analyzer.register_static_analyzer(adapter)

    result = await analyzer.analyze_file(str(test_file))

    # Should work and convert legacy format
    assert result.total_issues >= 1


@pytest.mark.asyncio
async def test_file_not_found(analyzer_config):
    """Test handling of non-existent files."""
    analyzer = CodeAnalyzer(analyzer_config)

    result = await analyzer.analyze_file("/nonexistent/path/file.c")

    assert result.total_issues >= 1
    assert "error" in result.issues_by_severity


@pytest.mark.asyncio
async def test_cpp_file_analysis(tmp_path, analyzer_config):
    """Test analysis of C++ files."""
    # Create a C++ test file
    test_file = tmp_path / "test.cpp"
    test_file.write_text("class Test { public: void run() {} };")

    analyzer = CodeAnalyzer(analyzer_config)

    result = await analyzer.analyze_file(str(test_file))

    assert isinstance(result, AnalysisReport)
    assert len(result.file_analyses) == 1
    assert result.file_analyses[0].language == "cpp"


@pytest.mark.asyncio
async def test_empty_file(tmp_path, analyzer_config):
    """Test analysis of empty file."""
    test_file = tmp_path / "empty.c"
    test_file.write_text("")

    analyzer = CodeAnalyzer(analyzer_config)

    result = await analyzer.analyze_file(str(test_file))

    assert result.total_issues == 0
    assert result.file_analyses[0].metrics.lines_of_code == 0


@pytest.mark.asyncio
async def test_multifunction_file(tmp_path, analyzer_config):
    """Test analysis of file with multiple functions."""
    test_file = tmp_path / "multi.c"
    test_file.write_text("""
int add(int a, int b) { return a + b; }
int sub(int a, int b) { return a - b; }
int main() { return add(1, 2); }
""")

    analyzer = CodeAnalyzer(analyzer_config)

    result = await analyzer.analyze_file(str(test_file))

    # Should detect 3 functions
    assert len(result.file_analyses) >= 1
    if result.file_analyses:
        func_count = result.file_analyses[0].metrics.function_count
        assert func_count == 3


@pytest.mark.asyncio
async def test_cyclomatic_complexity_metrics(tmp_path, analyzer_config):
    """Test AST-based cyclomatic complexity calculation."""
    # This code has a known complexity of 11
    # See manual calculation in comments
    code = """
#include <stdio.h>

// Complexity contributions:
// if (a > 0): +1
// if (b > 0): +1
// for loop: +1
void complex_function(int a, int b) {
    if (a > 0) {
        if (b > 0) {
            printf("Both positive\\n");
        } else {
            printf("A positive, B non-positive\\n");
        }
    }
    for (int i = 0; i < 10; i++) {
        printf("%d\\n", i);
    }
}

// Complexity contributions:
// while: +1
// &&: +1
// ||: +1
void logic_function(int x, int y, int z) {
    while (x > 0 && (y > 0 || z > 0)) {
        x--;
    }
}

// Complexity contributions:
// case 1: +1
// case 2: +1
// case 3: +1
// default (parsed as case_statement): +1
void switch_function(int opt) {
    switch (opt) {
        case 1: break;
        case 2: break;
        case 3: break;
        default: break;
    }
}
// Total Decision Points = 3 + 3 + 4 = 10
// Cyclomatic Complexity = 1 + Decision Points = 11
"""
    test_file = tmp_path / "complexity.c"
    test_file.write_text(code)

    analyzer = CodeAnalyzer(analyzer_config)
    result = await analyzer.analyze_file(str(test_file))

    assert len(result.file_analyses) == 1
    metrics = result.file_analyses[0].metrics

    # Check total complexity
    assert metrics.cyclomatic_complexity == 11

    # Also verify other metrics to ensure parser is working reasonably
    assert metrics.function_count == 3
    assert metrics.lines_of_code > 0
