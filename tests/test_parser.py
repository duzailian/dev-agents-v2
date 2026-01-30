import pytest
import os
from src.tools.code_analysis.parser import TreeSitterCodeParser
from src.models.code import CodeAnalysis

def test_parser_init():
    parser = TreeSitterCodeParser()
    assert parser is not None
    # We can't strictly assert parser.parser is None or not None because it depends on the environment
    # but we can check if build_dir is set correctly
    assert parser.build_dir == "build"

def test_parse_non_existent_file():
    parser = TreeSitterCodeParser()
    # Use a file that definitely doesn't exist
    result = parser.parse_file("non_existent_file_12345.c")
    assert isinstance(result, CodeAnalysis)
    assert len(result.issues) > 0
    assert "File not found" in result.issues[0].title

def test_parse_basic_file(tmp_path):
    # Create a dummy C file
    c_file = tmp_path / "test.c"
    content = """
    #include <stdio.h>

    int main() {
        printf("Hello World");
        return 0;
    }
    """
    c_file.write_text(content, encoding="utf-8")

    parser = TreeSitterCodeParser()
    result = parser.parse_file(str(c_file))

    assert isinstance(result, CodeAnalysis)
    assert result.metrics is not None
    # Content has 7 lines
    assert result.metrics.lines_of_code == 8
    assert str(c_file) in result.target_files

def test_parser_fallback_behavior(tmp_path):
    """Test that parser returns basic metrics even if tree-sitter fails or is not present."""
    # Create a dummy file
    c_file = tmp_path / "simple.c"
    c_file.write_text("int x = 1;", encoding="utf-8")

    parser = TreeSitterCodeParser()
    # Force parser to be None to simulate missing library
    parser.parser = None

    result = parser.parse_file(str(c_file))

    assert result.metrics.lines_of_code == 1
    # Should be 0 since parser was disabled
    assert result.metrics.function_count == 0
