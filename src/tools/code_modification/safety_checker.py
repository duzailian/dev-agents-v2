import re
from typing import Tuple, List

class SafetyChecker:
    """
    Checks code for potentially dangerous patterns using regex.
    """

    # Dangerous patterns to block (case-insensitive)
    DANGEROUS_PATTERNS = [
        (r'system\s*\(', "Usage of system() detected"),
        (r'exec[lv]?[pe]?\s*\(', "Usage of exec() family detected"),
        (r'popen\s*\(', "Usage of popen() detected"),
        (r'rm\s+-rf', "Dangerous 'rm -rf' command detected"),
        (r'mkfs', "Filesystem formatting command 'mkfs' detected"),
        (r'dd\s+if=', "Low-level disk copy 'dd if=' detected"),
    ]

    def check_security(self, code: str) -> Tuple[bool, List[str]]:
        """
        Checks the provided C/C++ code for dangerous patterns.

        Args:
            code: The source code string to check.

        Returns:
            A tuple (is_safe, warnings).
            is_safe: True if no dangerous patterns are found, False otherwise.
            warnings: A list of warning messages for found patterns.
        """
        warnings = []

        for pattern, message in self.DANGEROUS_PATTERNS:
            if re.search(pattern, code, re.IGNORECASE):
                warnings.append(message)

        is_safe = len(warnings) == 0
        return is_safe, warnings
