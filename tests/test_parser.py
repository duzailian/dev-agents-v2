import pytest
import os
from src.tools.code_analysis.parser import TreeSitterParser
from src.models.code import FunctionNode

# Sample C code for testing
SAMPLE_C_CODE = """
#include <stdio.h>

// A simple add function
int add(int a, int b) {
    return a + b;
}

void process_data(void) {
    int x = 10;
    int y = 20;
    int sum = add(x, y);
    printf("Sum: %d\\n", sum);
}

int main() {
    process_data();
    return 0;
}
"""

SAMPLE_CPP_CODE = """
#include <iostream>

class Calculator {
public:
    int multiply(int a, int b) {
        return a * b;
    }
};

int main() {
    Calculator calc;
    std::cout << calc.multiply(5, 6) << std::endl;
    return 0;
}
"""

class TestTreeSitterParser:

    def test_c_parsing(self):
        """Test parsing of standard C code"""
        parser = TreeSitterParser(language="c")
        tree = parser.parse(SAMPLE_C_CODE)
        assert tree is not None
        assert tree.root_node.type == "translation_unit"

    def test_c_function_extraction(self):
        """Test extraction of C functions"""
        parser = TreeSitterParser(language="c")
        functions = parser.extract_functions(SAMPLE_C_CODE, "test.c")

        # Should find: add, process_data, main
        assert len(functions) == 3

        # Verify 'add' function
        add_func = next((f for f in functions if f.name == "add"), None)
        assert add_func is not None
        assert add_func.return_type == "int"
        assert "int a" in add_func.parameters[0]["raw"]
        assert "int b" in add_func.parameters[0]["raw"]
        assert add_func.location.line == 5

        # Verify 'process_data' function
        proc_func = next((f for f in functions if f.name == "process_data"), None)
        assert proc_func is not None
        assert proc_func.return_type == "void"

    def test_c_call_extraction(self):
        """Test extraction of function calls"""
        parser = TreeSitterParser(language="c")
        calls = parser.extract_calls(SAMPLE_C_CODE)

        # Expect calls: add, printf, process_data
        call_names = [c["callee"] for c in calls]
        assert "add" in call_names
        assert "printf" in call_names
        assert "process_data" in call_names

        # Verify 'add' call details
        add_call = next((c for c in calls if c["callee"] == "add"), None)
        assert add_call is not None
        assert "x, y" in add_call["args"]

    def test_cpp_support(self):
        """Test basic C++ support"""
        parser = TreeSitterParser(language="cpp")
        functions = parser.extract_functions(SAMPLE_CPP_CODE, "test.cpp")

        # In C++ grammar, methods inside classes might need different queries
        # or the generic function_definition might capture them if they are top-level.
        # Note: Standard tree-sitter-cpp function_definition often captures top-level functions.
        # Methods inside classes are often `field_declaration` or `function_definition` nested.

        main_func = next((f for f in functions if f.name == "main"), None)
        assert main_func is not None
        assert main_func.return_type == "int"

    def test_invalid_language(self):
        """Test error handling for invalid languages"""
        with pytest.raises(ValueError):
            TreeSitterParser(language="invalid_lang")
