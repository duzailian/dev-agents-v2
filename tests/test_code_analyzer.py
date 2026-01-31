import pytest
import os
from pathlib import Path
from src.tools.code_analysis.analyzer import CodeAnalyzer
from src.models.code import AnalyzerConfig, AnalysisType

@pytest.fixture
def analyzer():
    config = AnalyzerConfig()
    return CodeAnalyzer(config)

@pytest.mark.asyncio
async def test_analyze_single_file_c(analyzer, tmp_path):
    # Create a dummy C file
    c_file = tmp_path / "test.c"
    c_file.write_text("""
    #include <stdio.h>

    int add(int a, int b) {
        return a + b;
    }

    int main() {
        int result = add(1, 2);
        return 0;
    }
    """, encoding="utf-8")

    report = await analyzer.analyze_files([str(c_file)])

    assert report is not None
    assert len(report.file_analyses) == 1

    analysis = report.file_analyses[0]
    assert analysis.language == "c"
    assert len(analysis.functions) >= 2 # add and main

    func_names = [f.name for f in analysis.functions]
    assert "add" in func_names
    assert "main" in func_names

    # Check includes
    assert "stdio.h" in analysis.includes[0]

@pytest.mark.asyncio
async def test_call_graph_integration(analyzer, tmp_path):
    c_file = tmp_path / "test_graph.c"
    c_file.write_text("""
    void funcB() {}
    void funcA() { funcB(); }
    int main() { funcA(); }
    """, encoding="utf-8")

    await analyzer.analyze_files([str(c_file)])

    # Check call graph
    cg = analyzer.call_graph

    # main calls funcA
    assert "funcA" in cg.get_callees("main")
    # funcA calls funcB
    assert "funcB" in cg.get_callees("funcA")

@pytest.mark.asyncio
async def test_metrics(analyzer, tmp_path):
    c_file = tmp_path / "test_metrics.c"
    code = """
    // Comment
    int func() {
        if (1) {
            return 1;
        }
        return 0;
    }
    """
    c_file.write_text(code, encoding="utf-8")

    analysis = await analyzer.analyze_single_file(str(c_file))
    metrics = analysis.metrics

    assert metrics.lines_of_code > 0
    assert metrics.lines_of_comments >= 1
    assert metrics.function_count == 1
    assert metrics.cyclomatic_complexity >= 2 # if + 1
