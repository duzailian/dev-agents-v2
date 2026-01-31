import subprocess
import re
import shutil
import xml.etree.ElementTree as ET
import os
from typing import List, Dict, Any, Optional, Protocol, runtime_checkable

from src.models.code import Issue, Location, IssueSeverity

@runtime_checkable
class StaticAnalyzer(Protocol):
    """Protocol for static analysis tools."""

    def analyze(self, file_paths: List[str]) -> List[Issue]:
        """Run analysis on the given files."""
        ...

    def get_version(self) -> str:
        """Get the version of the tool."""
        ...

class ClangTidyAnalyzer:
    """clang-tidy integration."""

    DEFAULT_CHECKS = [
        "bugprone-*",
        "cert-*",
        "clang-analyzer-*",
        "modernize-*",
        "performance-*",
        "readability-*",
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.binary_path = self.config.get("binary_path", "clang-tidy")
        self.checks = self.config.get("checks", self.DEFAULT_CHECKS)
        self.compile_commands_dir = self.config.get("compile_commands_dir")

    def is_available(self) -> bool:
        return shutil.which(self.binary_path) is not None

    def get_version(self) -> str:
        if not self.is_available():
            return "not found"
        try:
            result = subprocess.run(
                [self.binary_path, "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            # Extract version from string like "LLVM version 10.0.0"
            match = re.search(r"version\s+([\d\.]+)", result.stdout)
            return match.group(1) if match else "unknown"
        except subprocess.SubprocessError:
            return "error"

    def analyze(self, file_paths: List[str]) -> List[Issue]:
        if not self.is_available() or not file_paths:
            return []

        # We use standard text output because it's easier to parse without external deps
        # and --export-fixes requires a file or specific handling.
        # Format: file:line:col: severity: message [check-name]
        cmd = [
            self.binary_path,
            f"--checks={','.join(self.checks)}",
            # We don't use -warnings-as-errors so we can get all issues
        ]

        if self.compile_commands_dir:
            cmd.append(f"-p={self.compile_commands_dir}")

        cmd.extend(file_paths)

        try:
            # clang-tidy returns non-zero if issues are found often, so we don't check=True
            result = subprocess.run(cmd, capture_output=True, text=True)
            return self._parse_output(result.stdout)
        except Exception as e:
            # In a real app we might log this
            return []

    def _parse_output(self, output: str) -> List[Issue]:
        issues = []
        # Pattern: /path/to/file.c:10:5: warning: message [check-name]
        # Note: on Windows paths might contain :, so we need to be careful with the first colon
        # But usually clang-tidy outputs absolute paths or relative to execution.
        # Regex explanation:
        # ^(?P<file>.+?)  : File path (lazy match until next part)
        # :(?P<line>\d+)  : Line number
        # :(?P<col>\d+)   : Column number
        # :\s+(?P<severity>\w+) : Severity (warning, error, etc)
        # :\s+(?P<message>.+?)  : Message content
        # (?:\s+\[(?P<check>.+)\])?$ : Optional check name in brackets at end
        pattern = re.compile(r'^(?P<file>.+?):(?P<line>\d+):(?P<col>\d+):\s+(?P<severity>\w+):\s+(?P<message>.+?)(?:\s+\[(?P<check>.+)\])?$')

        for line in output.splitlines():
            match = pattern.match(line)
            if match:
                severity_str = match.group('severity').lower()
                # Map clang-tidy severity to IssueSeverity
                severity_map = {
                    'error': IssueSeverity.HIGH.value,
                    'warning': IssueSeverity.MEDIUM.value,
                    'info': IssueSeverity.INFO.value,
                    'note': IssueSeverity.INFO.value
                }

                issues.append(Issue(
                    rule_id=match.group('check') or "clang-tidy",
                    severity=severity_map.get(severity_str, IssueSeverity.LOW.value),
                    message=match.group('message'),
                    location=Location(
                        file_path=os.path.abspath(match.group('file')),
                        line=int(match.group('line')),
                        column=int(match.group('col'))
                    ),
                    category="static_analysis"
                ))
        return issues


class CppcheckAnalyzer:
    """cppcheck integration."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.binary_path = self.config.get("binary_path", "cppcheck")
        self.std = self.config.get("std", "c11")
        self.enable = self.config.get("enable", ["all"])

    def is_available(self) -> bool:
        return shutil.which(self.binary_path) is not None

    def get_version(self) -> str:
        if not self.is_available():
            return "not found"
        try:
            result = subprocess.run(
                [self.binary_path, "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            # Output: Cppcheck 2.3
            return result.stdout.strip().split(" ")[-1]
        except Exception:
            return "error"

    def analyze(self, file_paths: List[str]) -> List[Issue]:
        if not self.is_available() or not file_paths:
            return []

        cmd = [
            self.binary_path,
            f"--std={self.std}",
            f"--enable={','.join(self.enable)}",
            "--xml",
            "--xml-version=2"
        ]
        cmd.extend(file_paths)

        try:
            # cppcheck outputs xml to stderr
            result = subprocess.run(cmd, capture_output=True, text=True)
            return self._parse_xml_output(result.stderr)
        except Exception:
            return []

    def _parse_xml_output(self, output: str) -> List[Issue]:
        issues = []
        try:
            # Skip non-xml lines if any (sometimes tools output other stuff)
            # Find the first <results> or <cppcheck> tag
            xml_start = output.find('<?xml')
            if xml_start != -1:
                output = output[xml_start:]

            root = ET.fromstring(output)
            for error in root.findall('errors/error'):
                rule_id = error.get('id', 'cppcheck')
                msg = error.get('msg', '')
                severity_str = error.get('severity', 'style')

                # Map severity
                severity_map = {
                    'error': IssueSeverity.HIGH.value,
                    'warning': IssueSeverity.MEDIUM.value,
                    'style': IssueSeverity.LOW.value,
                    'performance': IssueSeverity.LOW.value,
                    'portability': IssueSeverity.LOW.value,
                    'information': IssueSeverity.INFO.value
                }

                # Cppcheck can list multiple locations for one error
                locations = error.findall('location')
                if locations:
                    # Take the first location
                    loc = locations[0]
                    file_path = loc.get('file', '')
                    line = int(loc.get('line', 0))
                    column = int(loc.get('column', 0))

                    issues.append(Issue(
                        rule_id=rule_id,
                        severity=severity_map.get(severity_str, IssueSeverity.LOW.value),
                        message=msg,
                        location=Location(
                            file_path=os.path.abspath(file_path),
                            line=line,
                            column=column
                        ),
                        category="static_analysis"
                    ))
        except ET.ParseError:
            pass

        return issues
