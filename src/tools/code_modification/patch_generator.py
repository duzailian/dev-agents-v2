import difflib
import os
from typing import List, Dict, Optional
from pathlib import Path

class PatchGenerator:
    """
    Generates unified diffs for code modifications.

    This class is responsible for comparing original and modified file contents
    and generating standard unified diff patches that can be applied using
    tools like 'git apply' or the CodeModifier class.
    """

    @staticmethod
    def generate_diff(original_content: str, modified_content: str, file_path: str) -> str:
        """
        Generate a unified diff between original and modified content for a single file.

        Args:
            original_content: The original file content.
            modified_content: The modified file content.
            file_path: The relative path to the file (used in diff headers).

        Returns:
            A string containing the unified diff.
        """
        original_lines = original_content.splitlines(keepends=True)
        modified_lines = modified_content.splitlines(keepends=True)

        # Ensure file path uses forward slashes for consistency in diffs
        clean_path = str(Path(file_path)).replace(os.sep, '/')

        # Calculate diff
        diff = difflib.unified_diff(
            original_lines,
            modified_lines,
            fromfile=f"a/{clean_path}",
            tofile=f"b/{clean_path}",
            lineterm=""
        )

        return "".join(diff)

    @staticmethod
    def generate_multi_file_diff(modifications: Dict[str, Dict[str, str]]) -> str:
        """
        Generate a single unified diff for multiple files.

        Args:
            modifications: A dictionary mapping file paths to a dict containing:
                - 'original': The original content
                - 'modified': The modified content

        Returns:
            A concatenated string of all unified diffs.
        """
        full_diff = []

        for file_path, contents in modifications.items():
            if 'original' not in contents or 'modified' not in contents:
                continue

            diff = PatchGenerator.generate_diff(
                contents['original'],
                contents['modified'],
                file_path
            )

            if diff:
                full_diff.append(diff)

        return "\n".join(full_diff)
