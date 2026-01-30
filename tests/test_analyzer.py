import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from src.tools.code_analysis.analyzer import CodeAnalyzer
from src.models.code import CodeAnalysis, CodeIssue, IssueSeverity, IssueType

# Mock the parser so we don't rely on FS or tree-sitter
class MockParser:
    def parse_file(self, file_path: str):
        return CodeAnalysis(target_files=[file_path])

@pytest.mark.asyncio
async def test_analyzer_basic_flow():
    mock_parser = MockParser()
    analyzer = CodeAnalyzer(parser=mock_parser)

    result = await analyzer.analyze_file("dummy.c")
    assert result.target_files == ["dummy.c"]
    assert len(result.issues) == 0

@pytest.mark.asyncio
async def test_analyzer_with_static_tool():
    mock_parser = MockParser()
    analyzer = CodeAnalyzer(parser=mock_parser)

    # Create a mock static analyzer
    mock_tool = MagicMock()
    # It must have an analyze method that returns a list of issues
    mock_tool.analyze = AsyncMock(return_value=[
        CodeIssue(title="Static Bug", severity=IssueSeverity.HIGH)
    ])

    analyzer.register_static_analyzer(mock_tool)

    result = await analyzer.analyze_file("dummy.c")

    mock_tool.analyze.assert_called_once_with("dummy.c")
    assert len(result.issues) == 1
    assert result.issues[0].title == "Static Bug"

@pytest.mark.asyncio
async def test_analyzer_with_ai_tool():
    mock_parser = MockParser()
    analyzer = CodeAnalyzer(parser=mock_parser)

    mock_ai = MagicMock()
    mock_ai.analyze = AsyncMock(return_value=[
        CodeIssue(title="AI Suggestion", severity=IssueSeverity.INFO)
    ])

    analyzer.set_ai_analyzer(mock_ai)

    result = await analyzer.analyze_file("dummy.c")

    mock_ai.analyze.assert_called_once()
    assert len(result.issues) == 1
    assert result.issues[0].title == "AI Suggestion"

@pytest.mark.asyncio
async def test_analyzer_exception_handling():
    # Test that exception in one tool doesn't crash the whole analysis
    mock_parser = MockParser()
    analyzer = CodeAnalyzer(parser=mock_parser)

    mock_tool_good = MagicMock()
    mock_tool_good.analyze = AsyncMock(return_value=[CodeIssue(title="Good")])

    mock_tool_bad = MagicMock()
    mock_tool_bad.analyze = AsyncMock(side_effect=Exception("Tool crashed"))

    analyzer.register_static_analyzer(mock_tool_good)
    analyzer.register_static_analyzer(mock_tool_bad)

    result = await analyzer.analyze_file("dummy.c")

    # We expect 2 issues: 1 from Good tool, 1 error report from Bad tool
    assert len(result.issues) == 2
    titles = [i.title for i in result.issues]
    assert "Good" in titles
    assert "Static Analysis Tool Error" in titles

@pytest.mark.asyncio
async def test_analyze_directory(tmp_path):
    mock_parser = MockParser()
    analyzer = CodeAnalyzer(parser=mock_parser)

    # Setup a fake directory structure
    d = tmp_path / "src"
    d.mkdir()
    (d / "a.c").write_text("code")
    (d / "b.h").write_text("header")
    (d / "readme.txt").write_text("text") # Should be ignored

    # We need to rely on the real file globbing in analyze_directory,
    # but we injected a mock parser. analyze_directory calls analyze_file.

    results = await analyzer.analyze_directory(str(d))

    assert len(results) == 2
    # Check that keys contain the filenames
    keys = list(results.keys())
    assert any("a.c" in k for k in keys)
    assert any("b.h" in k for k in keys)
    assert not any("readme.txt" in k for k in keys)
