import unittest
from unittest.mock import MagicMock, patch
import os
from src.models.code import IssueSeverity
from src.tools.code_analysis.static_analyzers import ClangTidyAnalyzer, CppcheckAnalyzer

class TestClangTidyAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = ClangTidyAnalyzer()

    @patch('subprocess.run')
    @patch('shutil.which')
    def test_analyze_success(self, mock_which, mock_run):
        mock_which.return_value = '/usr/bin/clang-tidy'

        # Mock output
        # /path/to/file.c:10:5: warning: message [check-name]
        output = "/abs/path/test.c:10:5: warning: potential memory leak [clang-analyzer-unix.Malloc]\n"
        output += "/abs/path/test.c:20:1: error: something wrong [misc-error]"

        mock_result = MagicMock()
        mock_result.stdout = output
        mock_result.return_value = 0
        mock_run.return_value = mock_result

        issues = self.analyzer.analyze(['test.c'])

        self.assertEqual(len(issues), 2)

        self.assertEqual(issues[0].rule_id, 'clang-analyzer-unix.Malloc')
        self.assertEqual(issues[0].severity, IssueSeverity.MEDIUM.value)
        self.assertEqual(issues[0].location.line, 10)

        self.assertEqual(issues[1].rule_id, 'misc-error')
        self.assertEqual(issues[1].severity, IssueSeverity.HIGH.value)

    @patch('subprocess.run')
    @patch('shutil.which')
    def test_get_version(self, mock_which, mock_run):
        mock_which.return_value = '/usr/bin/clang-tidy'
        mock_result = MagicMock()
        mock_result.stdout = "LLVM version 10.0.0"
        mock_result.return_value = 0
        mock_run.return_value = mock_result

        version = self.analyzer.get_version()
        self.assertEqual(version, "10.0.0")

    @patch('shutil.which')
    def test_not_available(self, mock_which):
        mock_which.return_value = None
        issues = self.analyzer.analyze(['test.c'])
        self.assertEqual(issues, [])

class TestCppcheckAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = CppcheckAnalyzer()

    @patch('subprocess.run')
    @patch('shutil.which')
    def test_analyze_xml_parsing(self, mock_which, mock_run):
        mock_which.return_value = '/usr/bin/cppcheck'

        xml_output = """<?xml version="1.0" encoding="UTF-8"?>
<results version="2">
    <cppcheck version="2.3"/>
    <errors>
        <error id="memleak" severity="error" msg="Memory leak: p" verbose="Memory leak: p">
            <location file="/abs/path/test.c" line="15" column="4"/>
        </error>
        <error id="style" severity="style" msg="Variable 'x' is assigned a value that is never used." verbose="Variable 'x' is assigned a value that is never used.">
            <location file="/abs/path/test.c" line="5" column="9"/>
        </error>
    </errors>
</results>
"""
        mock_result = MagicMock()
        mock_result.stderr = xml_output
        mock_result.return_value = 0
        mock_run.return_value = mock_result

        issues = self.analyzer.analyze(['test.c'])

        self.assertEqual(len(issues), 2)
        self.assertEqual(issues[0].rule_id, 'memleak')
        self.assertEqual(issues[0].severity, IssueSeverity.HIGH.value)
        self.assertEqual(issues[0].location.line, 15)

        self.assertEqual(issues[1].rule_id, 'style')
        self.assertEqual(issues[1].severity, IssueSeverity.LOW.value)

if __name__ == '__main__':
    unittest.main()
